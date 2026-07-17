"use client";

import { Box, Divider, Stack, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts";

import { formatMoney, formatNumber, formatPercent } from "@/lib/format";
import type { YearlyFinancials } from "@/lib/generated/models";

type MetricKey = "revenue" | "net_income" | "net_margin" | "ocf" | "capex" | "fcf" | "cf_per_share";

type MetricRow = {
  key: MetricKey;
  label: string;
  format: (value: number) => string;
};

const ROWS: MetricRow[] = [
  { key: "revenue", label: "Total Revenue", format: (v) => formatMoney(v) },
  { key: "net_income", label: "Net Income", format: (v) => formatMoney(v) },
  { key: "net_margin", label: "Net Profit Margin", format: (v) => formatPercent(v) },
  { key: "ocf", label: "Cash from Op. Act.", format: (v) => formatMoney(v) },
  { key: "capex", label: "CapEx", format: (v) => formatMoney(v) },
  { key: "fcf", label: "Free Cash Flow", format: (v) => formatMoney(v) },
  { key: "cf_per_share", label: "Cashflow / Share", format: (v) => formatNumber(v) },
];

// piecewise: negative bars red, positive blue — like the reference Financials panel
const SIGN_COLOR_MAP = {
  type: "piecewise" as const,
  thresholds: [0],
  colors: ["#f44336", "#1976d2"],
};

function latestValue(series: YearlyFinancials[], key: MetricKey): number | null {
  for (let index = series.length - 1; index >= 0; index -= 1) {
    const value = series[index][key];
    if (value != null) return value;
  }
  return null;
}

export function FinancialsPanel({ series }: { series: YearlyFinancials[] }) {
  const years = series.map((point) => point.fy);
  return (
    <Stack divider={<Divider />} spacing={1}>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr auto 140px",
          gap: 2,
          color: "text.secondary",
        }}
      >
        <Typography variant="subtitle2">Metric</Typography>
        <Typography variant="subtitle2">Current</Typography>
        <Typography variant="subtitle2" sx={{ textAlign: "right" }}>
          Trend {years[0]}–{years[years.length - 1]}
        </Typography>
      </Box>
      {ROWS.map((row) => {
        const current = latestValue(series, row.key);
        const values = series.map((point) => point[row.key]);
        const hasAny = values.some((value) => value != null);
        return (
          <Box
            key={row.key}
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr auto 140px",
              gap: 2,
              alignItems: "center",
            }}
          >
            <Typography>{row.label}</Typography>
            <Typography sx={{ fontWeight: 600 }}>
              {current === null ? "n/a" : row.format(current)}
            </Typography>
            <Box sx={{ justifySelf: "end", width: 140 }}>
              {hasAny ? (
                <BarChart
                  height={40}
                  xAxis={[{ data: years, scaleType: "band", position: "none" }]}
                  yAxis={[{ position: "none", colorMap: SIGN_COLOR_MAP }]}
                  series={[{ data: values }]}
                  margin={{ left: 0, right: 0, top: 2, bottom: 2 }}
                />
              ) : (
                <Typography variant="caption" color="text.secondary">
                  no data
                </Typography>
              )}
            </Box>
          </Box>
        );
      })}
    </Stack>
  );
}
