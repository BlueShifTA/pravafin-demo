"use client";

import {
  Box,
  Card,
  CardContent,
  Fade,
  Grid,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { LineChart, PieChart, RadarChart } from "@mui/x-charts";
import { useState } from "react";

import type { PortfolioHealth } from "@/lib/generated/models/portfolioHealth";
import type { PortfolioSummary } from "@/lib/generated/models/portfolioSummary";

import { PageShell } from "@/components/layout/PageShell";
import { Spinner } from "@/components/ui/feedback/Spinner";
import { formatPercent, moneyAxis } from "@/lib/format";
import { usePortfolioSummaryApiPortfoliosPortfolioIdSummaryGet } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

const currency = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

// Sleeve kinds are stored as core/satellite but shown to the user as ETF/Stock.
const KIND_LABEL: Record<string, string> = { core: "ETF", satellite: "Stock" };

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: "up" | "down";
}) {
  const subColor =
    accent === "up" ? "success.main" : accent === "down" ? "error.main" : "text.secondary";
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: "-0.01em" }}>
          {value}
        </Typography>
        {sub ? (
          <Typography variant="body2" sx={{ mt: 0.25, fontWeight: 600, color: subColor }}>
            {sub}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

const HEALTH_SHORT_LABEL: Record<string, string> = {
  allocation_discipline: "Allocation",
  sector_concentration: "Sector",
  region_concentration: "Region",
  cost_efficiency: "Cost",
  overlap: "Overlap",
  volatility: "Volatility",
};

function HealthCard({ health }: { health: PortfolioHealth }) {
  const available = health.criteria.filter((criterion) => criterion.score !== null);
  const unavailable = health.criteria.filter((criterion) => criterion.score === null);
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack direction="row" alignItems="baseline" spacing={1}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Portfolio health
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 700, color: "primary.main" }}>
            {health.headline.toFixed(1)}
            <Typography component="span" variant="body2" color="text.secondary">
              {" "}
              / 10
            </Typography>
          </Typography>
        </Stack>
        {available.length >= 3 ? (
          <RadarChart
            height={260}
            series={[{ data: available.map((criterion) => criterion.score ?? 0) }]}
            radar={{
              max: 10,
              metrics: available.map(
                (criterion) => HEALTH_SHORT_LABEL[criterion.key] ?? criterion.label
              ),
            }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Not enough data to score portfolio health yet.
          </Typography>
        )}
        {unavailable.length > 0 ? (
          <Typography variant="caption" color="text.secondary">
            n/a: {unavailable.map((criterion) => criterion.label).join(", ")} (no price history)
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

function EditableStatCard({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (next: number) => void;
}) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <TextField
          variant="standard"
          type="number"
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
          fullWidth
          slotProps={{
            input: {
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
              sx: { fontWeight: 700, fontSize: "1.35rem", letterSpacing: "-0.01em" },
            },
          }}
        />
      </CardContent>
    </Card>
  );
}

function futureValue(capital: number, annual: number, rate: number, years: number): number {
  const growth = (1 + rate) ** years;
  if (rate === 0) return capital + annual * years;
  return capital * growth + annual * ((growth - 1) / rate);
}

function DashboardBody({ summary }: { summary: PortfolioSummary }) {
  // Projection starts from the portfolio's real current value; invested (cost
  // basis) and monthly are the editable what-if inputs and drive the gain and
  // projection client-side (the backend rate stays fixed).
  const capital = summary.current_value;
  const [invested, setInvested] = useState<number>(summary.invested_total);
  const [monthly, setMonthly] = useState<number>(summary.monthly_contribution);

  const rate = summary.projections[0]?.annual_rate ?? 0;
  const years = summary.projections.map((projection) => projection.years);
  const project = (annualRate: number, y: number) =>
    futureValue(capital, monthly * 12, annualRate, y);

  const horizonYears = [0, ...years];
  const expected = [capital, ...years.map((y) => project(rate, y))];
  const low = [capital, ...years.map((y) => project(rate - 0.01, y))];
  const high = [capital, ...years.map((y) => project(rate + 0.01, y))];

  const gain = capital - invested;
  const gainPct = invested ? gain / invested : 0;

  return (
    <Fade in timeout={900}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <EditableStatCard label="Invested" value={invested} onChange={setInvested} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard
            label="Gain / loss"
            value={`${gain >= 0 ? "+" : "−"}$${currency.format(Math.abs(gain))}`}
            sub={`${gain >= 0 ? "+" : "−"}${formatPercent(Math.abs(gainPct))}`}
            accent={gain >= 0 ? "up" : "down"}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <EditableStatCard label="Monthly" value={monthly} onChange={setMonthly} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard
            label="Expected 10y"
            value={`$${currency.format(project(rate, 10))}`}
            sub={`${formatPercent(rate)}/yr`}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
          <StatCard
            label="Expected 20y"
            value={`$${currency.format(project(rate, 20))}`}
            sub={`${formatPercent(rate)}/yr`}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <HealthCard health={summary.health} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card variant="outlined" sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Allocation
              </Typography>
              <PieChart
                height={260}
                skipAnimation
                series={[
                  {
                    data: summary.allocation.map((slice, index) => ({
                      id: index,
                      value: slice.value,
                      label: `${slice.label} (${KIND_LABEL[slice.kind] ?? slice.kind})`,
                    })),
                    innerRadius: 50,
                  },
                ]}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid size={12}>
          <Card variant="outlined" sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Projection (weighted CAGR ±1%) — edit monthly to explore
              </Typography>
              <LineChart
                height={300}
                skipAnimation
                xAxis={[{ data: horizonYears, label: "years" }]}
                yAxis={[moneyAxis(Math.max(...high))]}
                series={[
                  { data: expected, label: "expected" },
                  { data: low, label: "low (−1%)" },
                  { data: high, label: "high (+1%)" },
                ]}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Fade>
  );
}

export default function DashboardPage() {
  const { portfolioId } = usePortfolio();
  const summaryQuery = usePortfolioSummaryApiPortfoliosPortfolioIdSummaryGet(portfolioId ?? 0, {
    query: { enabled: portfolioId !== null },
  });
  const summary = summaryQuery.data?.status === 200 ? summaryQuery.data.data : null;

  if (portfolioId === null) {
    return (
      <PageShell
        title="Dashboard"
        description="Pick a portfolio in the top bar — or create one via the wizard."
      >
        <Typography color="text.secondary">No portfolio selected.</Typography>
      </PageShell>
    );
  }
  if (summaryQuery.isLoading || !summary) {
    return (
      <PageShell title="Dashboard" description="Loading portfolio…">
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <Spinner size={40} />
        </Box>
      </PageShell>
    );
  }

  return (
    <PageShell title={summary.name} description="Current situation, allocation and projection.">
      <DashboardBody key={portfolioId} summary={summary} />
    </PageShell>
  );
}
