"use client";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Slider,
  Step,
  StepLabel,
  Stepper,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { PortfolioAssistant } from "@/components/wizard/PortfolioAssistant";
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
  const [coreFund, setCoreFund] = useState<string | null>(null);
  const [satellites, setSatellites] = useState<string[]>([]);

  const fundsQuery = useFundsApiMarketFundsGet();
  const funds = fundsQuery.data?.status === 200 ? fundsQuery.data.data : [];
  const screenerQuery = useScreenerApiMarketScreenerGet({ limit: 30 });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];
  const create = useCreatePortfolioApiPortfoliosPost();

  const satelliteWeight = satellites.length ? (1 - coreWeight) / satellites.length : 0;

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
          core: { fund_ticker: coreFund ?? "", weight: coreWeight },
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

  const stepValid =
    (step !== 0 || (name.length > 0 && capital > 0)) &&
    (step !== 1 || coreFund !== null) &&
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
            <Card variant="outlined">
              <CardContent sx={{ display: "grid", gap: 3, maxWidth: 420 }}>
                <AppTextField label="Name" value={name} onChange={(e) => setName(e.target.value)} />
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
          )}

          {step === 1 && (
            <Box
              sx={{
                display: "grid",
                gap: 2,
                gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              }}
            >
              {funds.map((fund) => (
                <Card
                  key={fund.ticker}
                  variant="outlined"
                  sx={{
                    cursor: "pointer",
                    borderColor: coreFund === fund.ticker ? "primary.main" : undefined,
                    borderWidth: coreFund === fund.ticker ? 2 : 1,
                  }}
                  onClick={() => setCoreFund(fund.ticker)}
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
              ))}
            </Box>
          )}

          {step === 2 && (
            <Card variant="outlined">
              <CardContent>
                <Typography sx={{ mb: 2 }} color="text.secondary">
                  Pick satellite stocks (magic-formula order — computed on the fly).
                </Typography>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                  {screener.map((row) => {
                    const selected = satellites.includes(row.ticker);
                    return (
                      <Button
                        key={row.ticker}
                        size="small"
                        variant={selected ? "contained" : "outlined"}
                        onClick={() =>
                          setSatellites(
                            selected
                              ? satellites.filter((ticker) => ticker !== row.ticker)
                              : [...satellites, row.ticker]
                          )
                        }
                      >
                        #{row.magic_rank} {row.ticker}
                      </Button>
                    );
                  })}
                </Box>
              </CardContent>
            </Card>
          )}

          {step === 3 && (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  Review
                </Typography>
                <Typography>
                  {name}: {formatMoney(capital)} + {formatMoney(monthly)}/month
                </Typography>
                <Typography>
                  Core {formatPercent(coreWeight, 0)} → {coreFund}
                </Typography>
                <Typography>
                  Satellites {formatPercent(1 - coreWeight, 0)} → {satellites.join(", ")} (
                  {formatPercent(satelliteWeight)} each)
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
