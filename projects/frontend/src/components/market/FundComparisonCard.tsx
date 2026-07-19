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
import { LineChart } from "@mui/x-charts";
import { useState } from "react";

import { Spinner } from "@/components/ui/feedback/Spinner";
import type { FundRow } from "@/lib/generated/models";
import { useCandlesApiMarketCandlesTickerGet } from "@/lib/generated/endpoints";

const COMPARE_DAYS = 1825; // 5 years

function closeByDate(bars: { date: string; close: number }[] | null): Map<string, number> {
  const map = new Map<string, number>();
  for (const bar of bars ?? []) map.set(bar.date, bar.close);
  return map;
}

// Overlay two funds' price growth, each normalised to 100 at the first shared
// date, so a fund's relative performance is comparable regardless of price.
export function FundComparisonCard({ funds }: { funds: FundRow[] }) {
  const [left, setLeft] = useState<string>("");
  const [right, setRight] = useState<string>("");

  const leftQuery = useCandlesApiMarketCandlesTickerGet(
    left,
    { days: COMPARE_DAYS },
    { query: { enabled: left !== "" } }
  );
  const rightQuery = useCandlesApiMarketCandlesTickerGet(
    right,
    { days: COMPARE_DAYS },
    { query: { enabled: right !== "" } }
  );
  const leftBars = leftQuery.data?.status === 200 ? leftQuery.data.data : null;
  const rightBars = rightQuery.data?.status === 200 ? rightQuery.data.data : null;

  const leftMap = closeByDate(leftBars);
  const rightMap = closeByDate(rightBars);
  const dates = [...leftMap.keys()].filter((date) => rightMap.has(date)).sort();
  const leftBase = dates.length ? (leftMap.get(dates[0]) ?? 0) : 0;
  const rightBase = dates.length ? (rightMap.get(dates[0]) ?? 0) : 0;
  const leftSeries = dates.map((date) => ((leftMap.get(date) ?? 0) / leftBase) * 100);
  const rightSeries = dates.map((date) => ((rightMap.get(date) ?? 0) / rightBase) * 100);

  const bothChosen = left !== "" && right !== "";
  const loading = bothChosen && (leftQuery.isLoading || rightQuery.isLoading);

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
            Compare two funds
          </Typography>
          <Stack direction="row" spacing={1.5}>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel id="compare-left">Fund A</InputLabel>
              <Select
                labelId="compare-left"
                label="Fund A"
                value={left}
                onChange={(event) => setLeft(String(event.target.value))}
              >
                {funds.map((fund) => (
                  <MenuItem key={fund.ticker} value={fund.ticker}>
                    {fund.ticker}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel id="compare-right">Fund B</InputLabel>
              <Select
                labelId="compare-right"
                label="Fund B"
                value={right}
                onChange={(event) => setRight(String(event.target.value))}
              >
                {funds.map((fund) => (
                  <MenuItem key={fund.ticker} value={fund.ticker}>
                    {fund.ticker}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </Box>
        {!bothChosen ? (
          <Typography color="text.secondary">Pick two funds to compare their growth.</Typography>
        ) : loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
            <Spinner size={32} />
          </Box>
        ) : dates.length === 0 ? (
          <Typography color="text.secondary">
            No overlapping price history for these funds.
          </Typography>
        ) : (
          <LineChart
            height={320}
            xAxis={[{ data: dates, scaleType: "point", label: "date" }]}
            yAxis={[{ label: "growth of 100" }]}
            series={[
              { data: leftSeries, label: left, showMark: false },
              { data: rightSeries, label: right, showMark: false },
            ]}
          />
        )}
      </CardContent>
    </Card>
  );
}
