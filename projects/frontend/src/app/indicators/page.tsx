"use client";

import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { LineChart } from "@mui/x-charts";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import {
  useIndicatorsApiMarketIndicatorsTickerGet,
  useScreenerApiMarketScreenerGet,
} from "@/lib/generated/endpoints";

const PERIODS = [
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
  { label: "180 days", value: 180 },
  { label: "1 year", value: 365 },
] as const;

// per-series palette ported from pravafin's indicators page
const COLORS = {
  close: "#1976d2",
  sma20: "#4caf50",
  sma50: "#ff9800",
  sma200: "#f44336",
  ema12: "#00bcd4",
  ema26: "#9c27b0",
  rsi: "#2196f3",
  macd: "#00bcd4",
  signal: "#ff5722",
} as const;

const DATE_FORMAT = new Intl.DateTimeFormat("en", { month: "short", day: "numeric" });

export default function IndicatorsPage() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [days, setDays] = useState<number>(180);

  const screenerQuery = useScreenerApiMarketScreenerGet({ limit: 500 });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];
  const ticker = selectedTicker ?? screener[0]?.ticker ?? null;

  const indicatorsQuery = useIndicatorsApiMarketIndicatorsTickerGet(
    ticker ?? "",
    { days },
    { query: { enabled: ticker !== null } }
  );
  const points = indicatorsQuery.data?.status === 200 ? indicatorsQuery.data.data : [];
  const dates = points.map((point) => new Date(point.date));
  const xAxis = [
    {
      data: dates,
      scaleType: "time" as const,
      valueFormatter: (value: Date) => DATE_FORMAT.format(value),
    },
  ];

  return (
    <PageShell
      title="Technical indicators"
      description="SMA, EMA, RSI and MACD computed on the fly from ingested daily prices — no stored derived tables."
    >
      <Box sx={{ display: "grid", gap: 2 }}>
        <Card variant="outlined">
          <CardContent sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel id="indicator-ticker">Symbol</InputLabel>
              <Select
                labelId="indicator-ticker"
                label="Symbol"
                value={ticker ?? ""}
                onChange={(event) => setSelectedTicker(String(event.target.value))}
              >
                {screener.map((row) => (
                  <MenuItem key={row.ticker} value={row.ticker}>
                    {row.ticker}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel id="indicator-period">Period</InputLabel>
              <Select
                labelId="indicator-period"
                label="Period"
                value={days}
                onChange={(event) => setDays(Number(event.target.value))}
              >
                {PERIODS.map((period) => (
                  <MenuItem key={period.value} value={period.value}>
                    {period.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Price &amp; moving averages
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Simple moving averages (20/50/200) smooth the trend; exponential averages (12/26)
              react faster to recent prices. Price above a rising SMA-200 is the classic long-term
              uptrend signal.
            </Typography>
            <LineChart
              height={340}
              xAxis={xAxis}
              series={[
                { data: points.map((p) => p.close), label: "Close", color: COLORS.close },
                { data: points.map((p) => p.sma_20), label: "SMA 20", color: COLORS.sma20 },
                { data: points.map((p) => p.sma_50), label: "SMA 50", color: COLORS.sma50 },
                { data: points.map((p) => p.sma_200), label: "SMA 200", color: COLORS.sma200 },
                { data: points.map((p) => p.ema_12), label: "EMA 12", color: COLORS.ema12 },
                { data: points.map((p) => p.ema_26), label: "EMA 26", color: COLORS.ema26 },
              ].map((series) => ({ ...series, showMark: false }))}
            />
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              RSI (14)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Relative Strength Index measures momentum on a 0–100 scale: below 30 is conventionally
              oversold, above 70 overbought.
            </Typography>
            <LineChart
              height={240}
              xAxis={xAxis}
              yAxis={[{ min: 0, max: 100 }]}
              series={[
                {
                  data: points.map((p) => p.rsi),
                  label: "RSI",
                  color: COLORS.rsi,
                  showMark: false,
                },
              ]}
            />
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              MACD (12/26/9)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              MACD is the gap between the 12- and 26-day EMAs; the signal line is its 9-day EMA.
              MACD crossing above the signal line is read as bullish momentum.
            </Typography>
            <LineChart
              height={240}
              xAxis={xAxis}
              series={[
                {
                  data: points.map((p) => p.macd),
                  label: "MACD",
                  color: COLORS.macd,
                  showMark: false,
                },
                {
                  data: points.map((p) => p.macd_signal),
                  label: "Signal",
                  color: COLORS.signal,
                  showMark: false,
                },
              ]}
            />
          </CardContent>
        </Card>
      </Box>
    </PageShell>
  );
}
