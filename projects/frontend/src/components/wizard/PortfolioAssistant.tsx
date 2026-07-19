"use client";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  LinearProgress,
  Typography,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { useState } from "react";

import type { ChatTurn, PortfolioDraft } from "@/lib/generated/models";
import {
  useFundsApiMarketFundsGet,
  useScreenerApiMarketScreenerGet,
} from "@/lib/generated/endpoints";
import { formatMoney, formatPercent } from "@/lib/format";
import { AGENT_TIMEOUT_MS, agentStageLabel, readSseEvents } from "@/lib/sse";
import { AppTextField } from "@/components/ui/fields/AppTextField";
import { StatBox } from "@/components/ui/StatBox";
import { Markdown } from "@/components/ui/Markdown";

const CONFIRM_MESSAGE = "Yes, build this portfolio.";

// Mirrors the guided wizard's "Review" step: weighted stat tiles plus a labeled
// row per holding. Weighted figures come from the same market data the wizard
// uses, keyed by the draft's tickers.
function DraftCard({ draft }: { draft: PortfolioDraft }) {
  const fundsQuery = useFundsApiMarketFundsGet();
  const funds = fundsQuery.data?.status === 200 ? fundsQuery.data.data : [];
  const screenerQuery = useScreenerApiMarketScreenerGet({ limit: 200 });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];

  const fundOf = (ticker: string) => funds.find((fund) => fund.ticker === ticker);
  const satOf = (ticker: string) => screener.find((row) => row.ticker === ticker);
  const weighted = (holdings: PortfolioDraft["cores"], value: (t: string) => number) => {
    const denom = holdings.reduce((sum, h) => sum + h.weight, 0);
    return denom ? holdings.reduce((sum, h) => sum + h.weight * value(h.ticker), 0) / denom : 0;
  };

  const coreTer = weighted(draft.cores, (t) => fundOf(t)?.ter ?? 0);
  const coreCagr = weighted(draft.cores, (t) => fundOf(t)?.cagr_10y ?? 0);
  const satelliteCagr = weighted(draft.satellites, (t) => satOf(t)?.cagr_10y ?? 0);
  const totalPct =
    (draft.cores.reduce((sum, c) => sum + c.weight, 0) +
      draft.satellites.reduce((sum, s) => sum + s.weight, 0)) *
    100;

  return (
    <Card variant="outlined">
      <CardContent sx={{ display: "grid", gap: 2 }}>
        <Box>
          <Typography sx={{ fontWeight: 700 }}>{draft.name}</Typography>
          <Typography variant="body2" color="text.secondary">
            {formatMoney(draft.initial_capital)} + {formatMoney(draft.monthly_contribution)}/month
          </Typography>
        </Box>
        <Box
          sx={{
            display: "grid",
            gap: 1.5,
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          }}
        >
          <StatBox label="ETF weighted TER" value={`${coreTer.toFixed(2)}%`} />
          <StatBox label="ETF weighted 10y CAGR" value={formatPercent(coreCagr)} />
          <StatBox label="Stock weighted 10y CAGR" value={formatPercent(satelliteCagr)} />
          <StatBox
            label="Total allocation"
            value={`${totalPct.toFixed(0)}%`}
            accent={Math.abs(totalPct - 100) < 0.5 ? "success.main" : "warning.main"}
          />
        </Box>
        <Divider />
        {draft.cores.map((core) => (
          <Box key={core.ticker} sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Chip label="ETF" size="small" color="primary" />
            <Typography sx={{ minWidth: 72, fontWeight: 600 }}>{core.ticker}</Typography>
            <Typography color="text.secondary">{formatPercent(core.weight, 0)}</Typography>
          </Box>
        ))}
        {draft.satellites.map((position) => (
          <Box key={position.ticker} sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Chip label="Stock" size="small" variant="outlined" />
            <Typography sx={{ minWidth: 72, fontWeight: 600 }}>{position.ticker}</Typography>
            <Typography color="text.secondary">{formatPercent(position.weight, 0)}</Typography>
          </Box>
        ))}
      </CardContent>
    </Card>
  );
}

export function PortfolioAssistant({ onCreated }: { onCreated: (portfolioId: number) => void }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState<PortfolioDraft | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [stage, setStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function send(message: string, confirm = false) {
    if (!message.trim() || sending) return;
    setError(null);
    setSending(true);
    setStage("Routing…");
    const history = turns;
    setTurns([...history, { role: "user", content: message }]);
    setInput("");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), AGENT_TIMEOUT_MS);
    try {
      const response = await fetch("/api/portfolio-draft/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history, proposed_draft: draft, confirm }),
        signal: controller.signal,
      });
      if (!response.ok || response.body == null) {
        setError(`Assistant failed (${response.status}).`);
        return;
      }
      for await (const { event, data } of readSseEvents(response.body)) {
        const nextStage = agentStageLabel(event, data);
        if (nextStage != null) setStage(nextStage);
        if (event === "answer") {
          const text = typeof data.text === "string" ? data.text : "";
          setTurns((prev) => [...prev, { role: "assistant", content: text }]);
          if (data.action === "propose" && data.draft) {
            setDraft(data.draft as PortfolioDraft);
          }
        } else if (event === "created") {
          onCreated(Number(data.portfolio_id));
          return;
        } else if (event === "error") {
          setError(String(data.message ?? "The assistant failed."));
        }
      }
    } catch {
      setError(
        controller.signal.aborted
          ? "The assistant timed out after 5 minutes."
          : "Assistant failed — is the backend running?"
      );
    } finally {
      clearTimeout(timer);
      setSending(false);
      setStage(null);
    }
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: { xs: "column", md: "row" },
        gap: 2,
        alignItems: { xs: "stretch", md: "flex-start" },
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "60vh",
          flexGrow: 1,
          maxWidth: 720,
        }}
      >
        <Typography variant="overline" color="text.secondary">
          Conversation
        </Typography>
        <Box
          sx={{
            flexGrow: 1,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 1.5,
            p: 1,
          }}
        >
          {turns.length === 0 && (
            <Typography color="text.secondary">
              Describe the portfolio you want — for example: &ldquo;60% ETF in tech and medical, 40%
              split across five high-upside stocks from different sectors.&rdquo;
            </Typography>
          )}
          {turns.map((turn, index) => (
            <Box
              key={index}
              sx={{
                alignSelf: turn.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "90%",
                px: 1.5,
                py: 1,
                borderRadius: 2,
                bgcolor: turn.role === "user" ? "primary.main" : "action.hover",
                color: turn.role === "user" ? "primary.contrastText" : "text.primary",
              }}
            >
              {turn.role === "user" ? (
                <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                  {turn.content}
                </Typography>
              ) : (
                <Markdown>{turn.content}</Markdown>
              )}
            </Box>
          ))}
          {sending && (
            <Box sx={{ alignSelf: "flex-start", minWidth: 200 }}>
              {stage != null && (
                <Typography variant="caption" color="text.secondary">
                  {stage}
                </Typography>
              )}
              <LinearProgress sx={{ mt: 0.5 }} />
            </Box>
          )}
          {error != null && <Alert severity="error">{error}</Alert>}
        </Box>
        <Box sx={{ display: "flex", gap: 1, alignItems: "center", pt: 1 }}>
          <AppTextField
            multiline
            maxRows={3}
            placeholder="Describe the portfolio you want…"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void send(input);
              }
            }}
            disabled={sending}
          />
          <Button
            aria-label="send message"
            variant="contained"
            onClick={() => void send(input)}
            disabled={sending || input.trim() === ""}
            sx={{ minWidth: 0, px: 2 }}
          >
            <SendIcon />
          </Button>
        </Box>
      </Box>

      {draft != null && (
        <Box
          sx={{
            width: { xs: "auto", md: 340 },
            flexShrink: 0,
            position: { xs: "static", md: "sticky" },
            top: 16,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Typography variant="overline" color="text.secondary">
            Proposed portfolio
          </Typography>
          <DraftCard draft={draft} />
          <Button
            fullWidth
            variant="contained"
            sx={{ mt: 1.5 }}
            disabled={sending}
            onClick={() => void send(CONFIRM_MESSAGE, true)}
          >
            Looks good — build it
          </Button>
        </Box>
      )}
    </Box>
  );
}
