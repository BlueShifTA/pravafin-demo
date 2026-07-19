"use client";

import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { CandleChart } from "@/components/market/CandleChart";
import { Spinner } from "@/components/ui/feedback/Spinner";
import {
  useCandlesApiMarketCandlesTickerGet,
  useIndicatorsApiMarketIndicatorsTickerGet,
} from "@/lib/generated/endpoints";

// Candle chart with range (1/2/5/10y) + interval (1D/7D/1M) selectors, shared by
// the satellite screener and the core fund view. Renders nothing without a ticker.
export function CandleChartCard({ ticker }: { ticker: string | null }) {
  const [chartDays, setChartDays] = useState<number>(365);
  const [chartInterval, setChartInterval] = useState<string>("1D");

  const barsQuery = useCandlesApiMarketCandlesTickerGet(
    ticker ?? "",
    { days: chartDays, interval: chartInterval },
    { query: { enabled: ticker !== null } }
  );
  const bars = barsQuery.data?.status === 200 ? barsQuery.data.data : null;
  const indicatorsQuery = useIndicatorsApiMarketIndicatorsTickerGet(
    ticker ?? "",
    { days: chartDays },
    { query: { enabled: ticker !== null } }
  );
  const indicators = indicatorsQuery.data?.status === 200 ? indicatorsQuery.data.data : undefined;

  if (ticker === null) return null;

  return (
    <Card variant="outlined">
      <CardContent>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 1.5,
            mb: 1,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {ticker} — candles
          </Typography>
          <Stack direction="row" spacing={1.5}>
            <FormControl size="small" sx={{ minWidth: 110 }}>
              <InputLabel id="chart-range">Range</InputLabel>
              <Select
                labelId="chart-range"
                label="Range"
                value={chartDays}
                onChange={(event) => setChartDays(Number(event.target.value))}
              >
                <MenuItem value={365}>1 year</MenuItem>
                <MenuItem value={730}>2 years</MenuItem>
                <MenuItem value={1825}>5 years</MenuItem>
                <MenuItem value={3650}>10 years</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 110 }}>
              <InputLabel id="chart-interval">Interval</InputLabel>
              <Select
                labelId="chart-interval"
                label="Interval"
                value={chartInterval}
                onChange={(event) => setChartInterval(String(event.target.value))}
              >
                <MenuItem value="1D">1 day</MenuItem>
                <MenuItem value="7D">7 days</MenuItem>
                <MenuItem value="1M">1 month</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </Box>
        {barsQuery.isLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
            <Spinner size={32} />
          </Box>
        ) : bars ? (
          <CandleChart bars={bars} indicators={chartInterval === "1D" ? indicators : undefined} />
        ) : (
          <Typography color="text.secondary">No price history for {ticker}.</Typography>
        )}
      </CardContent>
    </Card>
  );
}
