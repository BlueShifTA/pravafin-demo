"use client";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
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

function mean(values: number[]): number {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
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

  const fundsQuery = useFundsApiMarketFundsGet();
  const funds = fundsQuery.data?.status === 200 ? fundsQuery.data.data : [];
  const screenerQuery = useScreenerApiMarketScreenerGet({ limit: 200 });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];
  const create = useCreatePortfolioApiPortfoliosPost();

  // Core weight splits equally across the selected core ETFs; the remainder
  // splits equally across the selected satellites.
  const corePerWeight = coreFunds.length ? coreWeight / coreFunds.length : 0;
  const satelliteWeight = satellites.length ? (1 - coreWeight) / satellites.length : 0;

  const coreSelected = funds.filter((fund) => coreFunds.includes(fund.ticker));
  const satelliteSelected = screener.filter((row) => satellites.includes(row.ticker));
  const coreTer = mean(coreSelected.map((fund) => fund.ter ?? 0));
  const coreCagr = mean(coreSelected.map((fund) => fund.cagr_10y ?? 0));
  const satelliteCagr = mean(satelliteSelected.map((row) => row.cagr_10y ?? 0));

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
    create.mutate(
      {
        data: {
          name,
          initial_capital: capital,
          monthly_contribution: monthly,
          core: coreFunds.map((ticker) => ({ fund_ticker: ticker, weight: corePerWeight })),
          satellites: satellites.map((ticker) => ({
            ticker,
            weight: satelliteWeight,
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
        ? screener.map((row) => row.ticker).filter((ticker) => !ids.has(ticker))
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
                Select one or more core ETFs — {formatPercent(coreWeight, 0)} splits equally across
                them ({coreFunds.length} selected).
              </Typography>
              <Box
                sx={{
                  display: "grid",
                  gap: 2,
                  gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
                }}
              >
                {coreFiltered.map((fund) => {
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
                        <Typography variant="body2">
                          TER {fund.ter ?? "n/a"}% · 10y CAGR {formatPercent(fund.cagr_10y)}
                        </Typography>
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
            </Box>
          )}

          {step === 2 && (
            <Card variant="outlined">
              <CardContent>
                <Typography sx={{ mb: 2 }} color="text.secondary">
                  Pick satellite stocks — same magic-formula screener as the Satellite tab.
                </Typography>
                <DataGrid
                  rows={screener}
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
              <CardContent sx={{ display: "grid", gap: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Review
                </Typography>
                <Typography>
                  {name}: {formatMoney(capital)} + {formatMoney(monthly)}/month
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography sx={{ fontWeight: 600 }}>
                  Core sleeve — {formatPercent(coreWeight, 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {coreFunds.join(", ") || "none"} ({formatPercent(corePerWeight)} each)
                </Typography>
                <Typography variant="body2">
                  Weighted TER {coreTer.toFixed(2)}% · weighted 10y CAGR {formatPercent(coreCagr)}
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography sx={{ fontWeight: 600 }}>
                  Satellite sleeve — {formatPercent(1 - coreWeight, 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {satellites.join(", ") || "none"} ({formatPercent(satelliteWeight)} each)
                </Typography>
                <Typography variant="body2">
                  No TER (individual equities) · weighted 10y CAGR {formatPercent(satelliteCagr)}
                </Typography>
                {create.isError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {String(create.error)}
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          <Box sx={{ display: "flex", gap: 2, mt: 3 }}>
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
