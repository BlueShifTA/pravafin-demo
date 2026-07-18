"use client";

import { Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import { LineChart, PieChart, RadarChart } from "@mui/x-charts";

import type { PortfolioHealth } from "@/lib/generated/models/portfolioHealth";

import { PageShell } from "@/components/layout/PageShell";
import { formatPercent } from "@/lib/format";
import { usePortfolioSummaryApiPortfoliosPortfolioIdSummaryGet } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

const currency = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

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

export default function DashboardPage() {
  const { portfolioId } = usePortfolio();
  const summaryQuery = usePortfolioSummaryApiPortfoliosPortfolioIdSummaryGet(portfolioId ?? 0, {
    query: { enabled: portfolioId !== null },
  });
  const summary = summaryQuery.data?.status === 200 ? summaryQuery.data.data : null;

  if (portfolioId === null || !summary) {
    return (
      <PageShell
        title="Dashboard"
        description="Pick a portfolio in the top bar — or create one via the wizard."
      >
        <Typography color="text.secondary">No portfolio selected.</Typography>
      </PageShell>
    );
  }

  const horizonYears = [0, ...summary.projections.map((projection) => projection.years)];
  const expected = [summary.current_value, ...summary.projections.map((p) => p.expected)];
  const low = [summary.current_value, ...summary.projections.map((p) => p.low)];
  const high = [summary.current_value, ...summary.projections.map((p) => p.high)];

  const gain = summary.current_value - summary.invested_total;
  const gainPct = summary.invested_total ? gain / summary.invested_total : 0;
  const projectionFor = (years: number) =>
    summary.projections.find((projection) => projection.years === years) ?? null;
  const p10 = projectionFor(10);
  const p20 = projectionFor(20);

  return (
    <PageShell title={summary.name} description="Current situation, allocation and projection.">
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatCard label="Current value" value={`$${currency.format(summary.current_value)}`} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatCard label="Invested" value={`$${currency.format(summary.invested_total)}`} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatCard
            label="Gain / loss"
            value={`${gain >= 0 ? "+" : "−"}$${currency.format(Math.abs(gain))}`}
            sub={`${gain >= 0 ? "+" : "−"}${formatPercent(Math.abs(gainPct))}`}
            accent={gain >= 0 ? "up" : "down"}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatCard label="Monthly" value={`$${currency.format(summary.monthly_contribution)}`} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatCard
            label="Expected 10y"
            value={p10 ? `$${currency.format(p10.expected)}` : "n/a"}
            sub={p10 ? `${formatPercent(p10.annual_rate)}/yr` : undefined}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatCard
            label="Expected 20y"
            value={p20 ? `$${currency.format(p20.expected)}` : "n/a"}
            sub={p20 ? `${formatPercent(p20.annual_rate)}/yr` : undefined}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <HealthCard health={summary.health} />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card variant="outlined" sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Allocation
              </Typography>
              <PieChart
                height={260}
                series={[
                  {
                    data: summary.allocation.map((slice, index) => ({
                      id: index,
                      value: slice.value,
                      label: `${slice.label} (${slice.kind})`,
                    })),
                    innerRadius: 50,
                  },
                ]}
              />
              <Stack spacing={0.5}>
                {summary.drift.map((sleeve) => (
                  <Typography key={sleeve.kind} variant="body2" color="text.secondary">
                    {sleeve.kind}: {formatPercent(sleeve.actual_weight)} vs target{" "}
                    {formatPercent(sleeve.target_weight, 0)} (drift {formatPercent(sleeve.drift)})
                  </Typography>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card variant="outlined" sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Projection (weighted CAGR ±1%)
              </Typography>
              <LineChart
                height={300}
                xAxis={[{ data: horizonYears, label: "years" }]}
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
    </PageShell>
  );
}
