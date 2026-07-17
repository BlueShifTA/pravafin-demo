"use client";

import { Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import { LineChart, PieChart } from "@mui/x-charts";

import { PageShell } from "@/components/layout/PageShell";
import { usePortfolioSummaryApiPortfoliosPortfolioIdSummaryGet } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

const currency = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          {value}
        </Typography>
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

  return (
    <PageShell title={summary.name} description="Current situation, allocation and projection.">
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard label="Current value" value={`$${currency.format(summary.current_value)}`} />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard label="Invested" value={`$${currency.format(summary.invested_total)}`} />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard
            label="Monthly contribution"
            value={`$${currency.format(summary.monthly_contribution)}`}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 5 }}>
          <Card variant="outlined">
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
                    {sleeve.kind}: {(sleeve.actual_weight * 100).toFixed(1)}% vs target{" "}
                    {(sleeve.target_weight * 100).toFixed(0)}% (drift{" "}
                    {(sleeve.drift * 100).toFixed(1)}%)
                  </Typography>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card variant="outlined">
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
