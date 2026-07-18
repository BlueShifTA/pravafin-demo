-- CoreSat V1 schema. Idempotent — safe to re-apply.

DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'coresat_app') THEN
    CREATE ROLE coresat_app LOGIN PASSWORD 'coresat_app';
  END IF;
END $$;

-- pgvector powers the RAG document store (doc_chunks.embedding).
CREATE EXTENSION IF NOT EXISTS vector;

-- ── fact tables (shared, read-all) ─────────────────────────────

CREATE TABLE IF NOT EXISTS instruments (
    id          serial PRIMARY KEY,
    ticker      text NOT NULL UNIQUE,
    isin        text,
    name        text NOT NULL,
    type        text NOT NULL CHECK (type IN ('stock', 'etf')),
    sector      text,
    industry    text,
    region      text,
    currency    text NOT NULL DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS prices_daily (
    instrument_id integer NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date          date NOT NULL,
    open          numeric,
    high          numeric,
    low           numeric,
    close         numeric NOT NULL,
    volume        bigint,
    PRIMARY KEY (instrument_id, date)
);

CREATE TABLE IF NOT EXISTS funds (
    id          serial PRIMARY KEY,
    ticker      text NOT NULL UNIQUE,
    isin        text,
    name        text NOT NULL,
    provider    text,
    category    text,
    currency    text NOT NULL DEFAULT 'USD',
    fund_size   numeric,
    ter         numeric,
    dist_yield  numeric,
    cagr_5y     numeric,
    cagr_10y    numeric,
    valid_from  date NOT NULL DEFAULT current_date,
    valid_to    date
);

CREATE TABLE IF NOT EXISTS fund_holdings (
    fund_id  integer NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    ticker   text NOT NULL,
    name     text,
    weight   numeric,
    sector   text,
    region   text,
    PRIMARY KEY (fund_id, ticker)
);

CREATE TABLE IF NOT EXISTS fundamentals (
    instrument_id  integer PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    as_of          date NOT NULL DEFAULT current_date,
    pe_trailing    numeric,
    pe_forward     numeric,
    market_cap     numeric,
    revenue        numeric,
    net_profit     numeric,
    profit_margin  numeric,
    roe            numeric,
    dividend_yield numeric,
    beta           numeric,
    price_to_book  numeric,
    debt_to_equity numeric,
    free_cashflow  numeric,
    cagr_5y        numeric,
    cagr_10y       numeric,
    -- magic-formula inputs (latest fiscal year, SEC XBRL)
    ebit           numeric,
    nwc            numeric,
    ppe_net        numeric,
    cash           numeric,
    total_debt     numeric,
    shares         numeric
);

CREATE TABLE IF NOT EXISTS financials_yearly (
    instrument_id  integer NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    fy             integer NOT NULL,
    revenue        numeric,
    net_income     numeric,
    net_margin     numeric,
    ocf            numeric,
    capex          numeric,
    fcf            numeric,
    shares         numeric,
    PRIMARY KEY (instrument_id, fy)
);

-- RAG document store (shared fact table, read-all). One row per chunk with
-- page provenance; embedding is nomic-embed-text (768-d). tsv is a generated
-- full-text column for the BM25 half of hybrid search.
CREATE TABLE IF NOT EXISTS doc_chunks (
    id             serial PRIMARY KEY,
    source_doc     text NOT NULL,
    doc_type       text NOT NULL,
    instrument_id  integer REFERENCES instruments(id) ON DELETE CASCADE,
    fund_id        integer REFERENCES funds(id) ON DELETE CASCADE,
    page           integer,
    chunk_index    integer NOT NULL,
    text           text NOT NULL,
    embedding      vector(768),
    tsv            tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    checksum       text NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_doc, chunk_index)
);
CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx
    ON doc_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS doc_chunks_tsv_idx ON doc_chunks USING gin (tsv);

-- ── portfolio tables (RLS-protected) ───────────────────────────

CREATE TABLE IF NOT EXISTS portfolios (
    id                    serial PRIMARY KEY,
    name                  text NOT NULL,
    initial_capital       numeric NOT NULL,
    monthly_contribution  numeric NOT NULL DEFAULT 0,
    base_ccy              text NOT NULL DEFAULT 'USD',
    created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sleeves (
    id            serial PRIMARY KEY,
    portfolio_id  integer NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    kind          text NOT NULL CHECK (kind IN ('core', 'satellite')),
    target_weight numeric NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id              serial PRIMARY KEY,
    portfolio_id    integer NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    sleeve_id       integer NOT NULL REFERENCES sleeves(id) ON DELETE CASCADE,
    instrument_id   integer REFERENCES instruments(id),
    fund_id         integer REFERENCES funds(id),
    target_weight   numeric NOT NULL,
    invested_amount numeric NOT NULL,
    acquired_at     date NOT NULL DEFAULT current_date,
    CHECK (instrument_id IS NOT NULL OR fund_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS llm_audit_log (
    id            serial PRIMARY KEY,
    portfolio_id  integer NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    feature       text NOT NULL,
    model         text NOT NULL,
    tokens_in     integer NOT NULL DEFAULT 0,
    tokens_out    integer NOT NULL DEFAULT 0,
    cost          numeric,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Copilot graph runs audit per node; single-call features leave these NULL.
ALTER TABLE llm_audit_log ADD COLUMN IF NOT EXISTS graph_run_id text;
ALTER TABLE llm_audit_log ADD COLUMN IF NOT EXISTS node text;

CREATE TABLE IF NOT EXISTS chat_messages (
    id            serial PRIMARY KEY,
    portfolio_id  integer NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    role          text NOT NULL CHECK (role IN ('user', 'assistant')),
    content       text NOT NULL,
    citations     jsonb NOT NULL DEFAULT '[]'::jsonb,
    tokens_in     integer NOT NULL DEFAULT 0,
    tokens_out    integer NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ── ingestion ops ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ingest_runs (
    id                serial PRIMARY KEY,
    source            text NOT NULL,
    adapter_version   text NOT NULL DEFAULT '1',
    status            text NOT NULL DEFAULT 'running',
    rows_in           integer NOT NULL DEFAULT 0,
    rows_ok           integer NOT NULL DEFAULT 0,
    rows_quarantined  integer NOT NULL DEFAULT 0,
    checksum          text UNIQUE,
    started_at        timestamptz NOT NULL DEFAULT now(),
    finished_at       timestamptz
);

CREATE TABLE IF NOT EXISTS ingest_quarantine (
    id          serial PRIMARY KEY,
    run_id      integer NOT NULL REFERENCES ingest_runs(id) ON DELETE CASCADE,
    source      text NOT NULL,
    payload     jsonb NOT NULL,
    reason      text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- ── row-level security (portfolio tables only) ─────────────────
-- Context comes from set_config('app.portfolio_id', ..., true) inside the
-- request transaction (SET LOCAL semantics — dies at commit, pool-safe).
-- missing_ok=true: unset context ⇒ NULL ⇒ no rows, never an error.
-- WITH CHECK: writes cannot smuggle a foreign portfolio_id.

ALTER TABLE portfolios    ENABLE ROW LEVEL SECURITY;
ALTER TABLE sleeves       ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- portfolios: creation goes through create_portfolio() (SECURITY DEFINER)
-- because INSERT..RETURNING is subject to SELECT policies — the fresh row is
-- invisible before a scope exists. All direct access is scoped.
DROP POLICY IF EXISTS per_portfolio_self ON portfolios;
DROP POLICY IF EXISTS portfolios_insert ON portfolios;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_policies
                 WHERE tablename = 'portfolios' AND policyname = 'portfolios_select') THEN
    CREATE POLICY portfolios_select ON portfolios FOR SELECT
      USING (id = current_setting('app.portfolio_id', true)::int);
    CREATE POLICY portfolios_update ON portfolios FOR UPDATE
      USING      (id = current_setting('app.portfolio_id', true)::int)
      WITH CHECK (id = current_setting('app.portfolio_id', true)::int);
    CREATE POLICY portfolios_delete ON portfolios FOR DELETE
      USING (id = current_setting('app.portfolio_id', true)::int);
  END IF;
  IF NOT EXISTS (SELECT FROM pg_policies
                 WHERE tablename = 'sleeves' AND policyname = 'per_portfolio') THEN
    CREATE POLICY per_portfolio ON sleeves
      USING      (portfolio_id = current_setting('app.portfolio_id', true)::int)
      WITH CHECK (portfolio_id = current_setting('app.portfolio_id', true)::int);
  END IF;
  IF NOT EXISTS (SELECT FROM pg_policies
                 WHERE tablename = 'positions' AND policyname = 'per_portfolio') THEN
    CREATE POLICY per_portfolio ON positions
      USING      (portfolio_id = current_setting('app.portfolio_id', true)::int)
      WITH CHECK (portfolio_id = current_setting('app.portfolio_id', true)::int);
  END IF;
  IF NOT EXISTS (SELECT FROM pg_policies
                 WHERE tablename = 'llm_audit_log' AND policyname = 'per_portfolio') THEN
    CREATE POLICY per_portfolio ON llm_audit_log
      USING      (portfolio_id = current_setting('app.portfolio_id', true)::int)
      WITH CHECK (portfolio_id = current_setting('app.portfolio_id', true)::int);
  END IF;
  IF NOT EXISTS (SELECT FROM pg_policies
                 WHERE tablename = 'chat_messages' AND policyname = 'per_portfolio') THEN
    CREATE POLICY per_portfolio ON chat_messages
      USING      (portfolio_id = current_setting('app.portfolio_id', true)::int)
      WITH CHECK (portfolio_id = current_setting('app.portfolio_id', true)::int);
  END IF;
END $$;

CREATE OR REPLACE FUNCTION create_portfolio(
    p_name text,
    p_capital numeric,
    p_contribution numeric DEFAULT 0,
    p_base_ccy text DEFAULT 'USD'
) RETURNS integer
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    INSERT INTO portfolios (name, initial_capital, monthly_contribution, base_ccy)
    VALUES (p_name, p_capital, p_contribution, p_base_ccy)
    RETURNING id;
$$;
REVOKE ALL ON FUNCTION create_portfolio(text, numeric, numeric, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION create_portfolio(text, numeric, numeric, text) TO coresat_app;

-- Selector metadata for the portfolio switcher (single-user demo: names are not
-- sensitive; row contents stay RLS-guarded).
CREATE OR REPLACE FUNCTION list_portfolios()
RETURNS TABLE (id integer, name text, created_at timestamptz)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT id, name, created_at FROM portfolios ORDER BY id;
$$;
REVOKE ALL ON FUNCTION list_portfolios() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION list_portfolios() TO coresat_app;

-- ── grants ──────────────────────────────────────────────────────

GRANT USAGE ON SCHEMA public TO coresat_app;
GRANT SELECT ON instruments, prices_daily, funds, fund_holdings, fundamentals,
    financials_yearly, doc_chunks TO coresat_app;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON portfolios, sleeves, positions, llm_audit_log TO coresat_app;
GRANT SELECT, INSERT, DELETE ON chat_messages TO coresat_app;
GRANT SELECT, INSERT ON ingest_runs, ingest_quarantine TO coresat_app;
GRANT UPDATE ON ingest_runs TO coresat_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO coresat_app;
