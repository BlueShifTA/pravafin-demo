"use client";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Pagination,
  Slider,
  Stack,
  Step,
  StepLabel,
  Stepper,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import type { GridRowSelectionModel } from "@mui/x-data-grid";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { PortfolioAssistant } from "@/components/wizard/PortfolioAssistant";
import { screenerColumns } from "@/components/market/screenerColumns";
import { formatMoney, formatPercent } from "@/lib/format";
import { AppTextField } from "@/components/ui/fields/AppTextField";
import {
  getListPortfoliosApiPortfoliosGetQueryKey,
  useCreatePortfolioApiPortfoliosPost,
  useFundsApiMarketFundsGet,
  useScreenerApiMarketScreenerGet,
} from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

const STEPS = ["Capital", "Core ETF", "Satellites", "Review"] as const;
const CORE_PAGE_SIZE = 12; // 4 columns x 3 rows

function StatBox({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: 700, color: accent }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function WizardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setPortfolioId } = usePortfolio();
  const [mode, setMode] = useState<"wizard" | "assistant">("wizard");
  const [step, setStep] = useState(0);
  const [name, setName] = useState("My portfolio");
  const [capital, setCapital] = useState(10_000);
  const [monthly, setMonthly] = useState(200);
  const [coreWeight, setCoreWeight] = useState(0.8);
  const [coreFunds, setCoreFunds] = useState<string[]>([]);
  const [satellites, setSatellites] = useState<string[]>([]);
  const [coreSearch, setCoreSearch] = useState("");
  const [maxTer, setMaxTer] = useState("");
  const [minCagr, setMinCagr] = useState("");
  const [corePage, setCorePage] = useState(1);
  const [satSearch, setSatSearch] = useState("");
  // Per-item weight overrides (percent of the whole portfolio); absent = the
  // equal split implied by the core/satellite slider.
  const [coreWeights, setCoreWeights] = useState<Record<string, number>>({});
  const [satWeights, setSatWeights] = useState<Record<string, number>>({});

  const fundsQuery = useFundsApiMarketFundsGet();
  const funds = fundsQuery.data?.status === 200 ? fundsQuery.data.data : [];
  const screenerQuery = useScreenerApiMarketScreenerGet({ limit: 200 });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];
  const create = useCreatePortfolioApiPortfoliosPost();

  const defaultCorePct = coreFunds.length ? (coreWeight * 100) / coreFunds.length : 0;
  const defaultSatPct = satellites.length ? ((1 - coreWeight) * 100) / satellites.length : 0;
  const corePct = (ticker: string) => coreWeights[ticker] ?? defaultCorePct;
  const satPct = (ticker: string) => satWeights[ticker] ?? defaultSatPct;
  const totalPct =
    coreFunds.reduce((sum, ticker) => sum + corePct(ticker), 0) +
    satellites.reduce((sum, ticker) => sum + satPct(ticker), 0);

  const fundOf = (ticker: string) => funds.find((fund) => fund.ticker === ticker);
  const satOf = (ticker: string) => screener.find((row) => row.ticker === ticker);
  const weighted = (
    tickers: string[],
    pct: (t: string) => number,
    value: (t: string) => number
  ) => {
    const denom = tickers.reduce((sum, ticker) => sum + pct(ticker), 0);
    return denom
      ? tickers.reduce((sum, ticker) => sum + pct(ticker) * value(ticker), 0) / denom
      : 0;
  };
  const coreTer = weighted(coreFunds, corePct, (t) => fundOf(t)?.ter ?? 0);
  const coreCagr = weighted(coreFunds, corePct, (t) => fundOf(t)?.cagr_10y ?? 0);
  const satelliteCagr = weighted(satellites, satPct, (t) => satOf(t)?.cagr_10y ?? 0);

  const coreFiltered = funds.filter((fund) => {
    const query = coreSearch.trim().toLowerCase();
    const matchesText =
      query === "" ||
      fund.ticker.toLowerCase().includes(query) ||
      (fund.name ?? "").toLowerCase().includes(query);
    const matchesTer = maxTer === "" || (fund.ter ?? Infinity) <= Number(maxTer);
    const matchesCagr = minCagr === "" || (fund.cagr_10y ?? -Infinity) >= Number(minCagr) / 100;
    return matchesText && matchesTer && matchesCagr;
  });
  const corePageCount = Math.max(1, Math.ceil(coreFiltered.length / CORE_PAGE_SIZE));
  const corePageSafe = Math.min(corePage, corePageCount);
  const coreVisible = coreFiltered.slice(
    (corePageSafe - 1) * CORE_PAGE_SIZE,
    corePageSafe * CORE_PAGE_SIZE
  );

  const satRows = screener.filter((row) => {
    const query = satSearch.trim().toLowerCase();
    return (
      query === "" ||
      row.ticker.toLowerCase().includes(query) ||
      (row.name ?? "").toLowerCase().includes(query) ||
      (row.sector ?? "").toLowerCase().includes(query)
    );
  });

  // Both creation paths (guided wizard, AI assistant) land here: the header
  // selector's list query is already mounted, so without invalidation it keeps
  // serving the stale list without the new row.
  const onCreated = (portfolioId: number) => {
    void queryClient.invalidateQueries({
      queryKey: getListPortfoliosApiPortfoliosGetQueryKey(),
    });
    setPortfolioId(portfolioId);
    router.push("/");
  };

  const submit = () => {
    if (totalPct <= 0) return;
    create.mutate(
      {
        data: {
          name,
          initial_capital: capital,
          monthly_contribution: monthly,
          // normalize the adjusted proportions to sum to 1
          core: coreFunds.map((ticker) => ({
            fund_ticker: ticker,
            weight: corePct(ticker) / totalPct,
          })),
          satellites: satellites.map((ticker) => ({
            ticker,
            weight: satPct(ticker) / totalPct,
            acquired_at: null,
          })),
        },
      },
      {
        onSuccess: (created) => {
          if (created.status !== 201) return;
          onCreated(created.data.id);
        },
      }
    );
  };

  const toggleCoreFund = (ticker: string) => {
    setCoreFunds((current) =>
      current.includes(ticker) ? current.filter((value) => value !== ticker) : [...current, ticker]
    );
  };

  const onSatelliteSelection = (model: GridRowSelectionModel) => {
    // DataGrid represents "select all" as an exclude-model (ids = the unchecked
    // rows), so resolve it against the visible rows instead of trusting ids alone.
    const ids = new Set([...(model.ids ?? [])].map(String));
    const selected =
      model.type === "exclude"
        ? satRows.map((row) => row.ticker).filter((ticker) => !ids.has(ticker))
        : [...ids];
    setSatellites(selected);
  };

  const stepValid =
    (step !== 0 || (name.length > 0 && capital > 0)) &&
    (step !== 1 || coreFunds.length > 0) &&
    (step !== 2 || satellites.length > 0);

  return (
    <PageShell
      title="New portfolio"
      description="Build it step by step, or describe it to the assistant."
    >
      <ToggleButtonGroup
        exclusive
        size="small"
        value={mode}
        onChange={(_, next) => {
          if (next === "wizard" || next === "assistant") setMode(next);
        }}
        sx={{ mb: 4 }}
      >
        <ToggleButton value="wizard">Guided wizard</ToggleButton>
        <ToggleButton value="assistant">AI assistant</ToggleButton>
      </ToggleButtonGroup>

      {mode === "assistant" && <PortfolioAssistant onCreated={onCreated} />}

      {mode === "wizard" && (
        <>
          <Stepper activeStep={step} sx={{ mb: 4 }}>
            {STEPS.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {step === 0 && (
            <Box sx={{ display: "flex", justifyContent: "center" }}>
              <Card variant="outlined" sx={{ width: "100%", maxWidth: 480 }}>
                <CardContent sx={{ display: "grid", gap: 3 }}>
                  <AppTextField
                    label="Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <AppTextField
                    label="Initial capital (USD)"
                    type="number"
                    value={capital}
                    onChange={(e) => setCapital(Number(e.target.value))}
                  />
                  <AppTextField
                    label="Monthly contribution (USD)"
                    type="number"
                    value={monthly}
                    onChange={(e) => setMonthly(Number(e.target.value))}
                  />
                  <Box>
                    <Typography gutterBottom>
                      Core weight: {formatPercent(coreWeight, 0)} (satellites{" "}
                      {formatPercent(1 - coreWeight, 0)})
                    </Typography>
                    <Slider
                      value={coreWeight}
                      min={0.5}
                      max={0.95}
                      step={0.05}
                      onChange={(_, value) => setCoreWeight(value as number)}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Box>
          )}

          {step === 1 && (
            <Box sx={{ display: "grid", gap: 2 }}>
              <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", rowGap: 2 }}>
                <AppTextField
                  label="Search ETFs"
                  value={coreSearch}
                  onChange={(e) => setCoreSearch(e.target.value)}
                  sx={{ flex: 1, minWidth: 220 }}
                />
                <AppTextField
                  label="Max TER (%)"
                  type="number"
                  value={maxTer}
                  onChange={(e) => setMaxTer(e.target.value)}
                  sx={{ width: 150 }}
                />
                <AppTextField
                  label="Min 10y CAGR (%)"
                  type="number"
                  value={minCagr}
                  onChange={(e) => setMinCagr(e.target.value)}
                  sx={{ width: 170 }}
                />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Select one or more core ETFs — {formatPercent(coreWeight, 0)} splits across them (
                {coreFunds.length} selected).
              </Typography>
              <Box
                sx={{
                  display: "grid",
                  gap: 2,
                  gridTemplateColumns: { xs: "repeat(2, 1fr)", md: "repeat(4, 1fr)" },
                }}
              >
                {coreVisible.map((fund) => {
                  const selected = coreFunds.includes(fund.ticker);
                  return (
                    <Card
                      key={fund.ticker}
                      variant="outlined"
                      sx={{
                        cursor: "pointer",
                        borderColor: selected ? "primary.main" : undefined,
                        borderWidth: selected ? 2 : 1,
                      }}
                      onClick={() => toggleCoreFund(fund.ticker)}
                    >
                      <CardContent>
                        <Typography sx={{ fontWeight: 600 }}>{fund.ticker}</Typography>
                        <Typography variant="body2" color="text.secondary" noWrap>
                          {fund.name}
                        </Typography>
                        <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              TER
                            </Typography>
                            <Typography sx={{ fontWeight: 700, color: "primary.main" }}>
                              {fund.ter ?? "n/a"}%
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              10y CAGR
                            </Typography>
                            <Typography sx={{ fontWeight: 700, color: "success.main" }}>
                              {formatPercent(fund.cagr_10y)}
                            </Typography>
                          </Box>
                        </Stack>
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
              {corePageCount > 1 && (
                <Box sx={{ display: "flex", justifyContent: "center", mt: 1 }}>
                  <Pagination
                    count={corePageCount}
                    page={corePageSafe}
                    onChange={(_, value) => setCorePage(value)}
                  />
                </Box>
              )}
            </Box>
          )}

          {step === 2 && (
            <Card variant="outlined">
              <CardContent sx={{ display: "grid", gap: 2 }}>
                <Typography color="text.secondary">
                  Pick satellite stocks — same magic-formula screener as the Satellite tab.
                </Typography>
                <AppTextField
                  label="Search stocks"
                  value={satSearch}
                  onChange={(e) => setSatSearch(e.target.value)}
                  sx={{ maxWidth: 320 }}
                />
                <DataGrid
                  rows={satRows}
                  columns={screenerColumns}
                  getRowId={(row) => row.ticker}
                  loading={screenerQuery.isLoading}
                  checkboxSelection
                  rowSelectionModel={{ type: "include", ids: new Set<string>(satellites) }}
                  onRowSelectionModelChange={onSatelliteSelection}
                  density="compact"
                  initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
                  pageSizeOptions={[10, 25, 50, 100]}
                  sx={{ height: 480 }}
                />
              </CardContent>
            </Card>
          )}

          {step === 3 && (
            <Card variant="outlined">
              <CardContent sx={{ display: "grid", gap: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Review
                </Typography>
                <Typography>
                  {name}: {formatMoney(capital)} + {formatMoney(monthly)}/month
                </Typography>
                <Box
                  sx={{
                    display: "grid",
                    gap: 2,
                    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                  }}
                >
                  <StatBox label="Core weighted TER" value={`${coreTer.toFixed(2)}%`} />
                  <StatBox label="Core weighted 10y CAGR" value={formatPercent(coreCagr)} />
                  <StatBox
                    label="Satellite weighted 10y CAGR"
                    value={formatPercent(satelliteCagr)}
                  />
                  <StatBox
                    label="Total allocation"
                    value={`${totalPct.toFixed(0)}%`}
                    accent={Math.abs(totalPct - 100) < 0.5 ? "success.main" : "warning.main"}
                  />
                </Box>
                <Divider />
                <Typography sx={{ fontWeight: 600 }}>Adjust proportions</Typography>
                {coreFunds.map((ticker) => (
                  <Box key={ticker} sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <Chip label="core" size="small" color="primary" />
                    <Typography sx={{ minWidth: 90, fontWeight: 600 }}>{ticker}</Typography>
                    <AppTextField
                      type="number"
                      value={Number(corePct(ticker).toFixed(1))}
                      onChange={(e) =>
                        setCoreWeights({ ...coreWeights, [ticker]: Number(e.target.value) })
                      }
                      sx={{ width: 120 }}
                    />
                    <Typography color="text.secondary">%</Typography>
                  </Box>
                ))}
                {satellites.map((ticker) => (
                  <Box key={ticker} sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <Chip label="satellite" size="small" variant="outlined" />
                    <Typography sx={{ minWidth: 90, fontWeight: 600 }}>{ticker}</Typography>
                    <AppTextField
                      type="number"
                      value={Number(satPct(ticker).toFixed(1))}
                      onChange={(e) =>
                        setSatWeights({ ...satWeights, [ticker]: Number(e.target.value) })
                      }
                      sx={{ width: 120 }}
                    />
                    <Typography color="text.secondary">%</Typography>
                  </Box>
                ))}
                {Math.abs(totalPct - 100) >= 0.5 && (
                  <Typography variant="body2" color="warning.main">
                    Weights sum to {totalPct.toFixed(1)}% — they will be normalized to 100% on
                    create.
                  </Typography>
                )}
                {create.isError && <Alert severity="error">{String(create.error)}</Alert>}
              </CardContent>
            </Card>
          )}

          <Box
            sx={{
              display: "flex",
              gap: 2,
              mt: 3,
              justifyContent: "space-between",
              ...(step === 0 ? { maxWidth: 480, mx: "auto", justifyContent: "flex-start" } : {}),
            }}
          >
            <Button disabled={step === 0} onClick={() => setStep(step - 1)}>
              Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button variant="contained" disabled={!stepValid} onClick={() => setStep(step + 1)}>
                Next
              </Button>
            ) : (
              <Button variant="contained" disabled={create.isPending} onClick={submit}>
                Create portfolio
              </Button>
            )}
          </Box>
        </>
      )}
    </PageShell>
  );
}
