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

import type { FundRow } from "@/lib/generated/models";
import { formatMoney, formatMoneyCompact, formatPercent } from "@/lib/format";

const CAPITAL = 10_000;
const YEARS = 20;
const HORIZON = Array.from({ length: YEARS + 1 }, (_, year) => year);

// Net-of-fees growth rate: the fund's CAGR minus its TER (TER is stored as a
// percent number, e.g. 0.2 -> 0.2%).
function netRate(fund: FundRow | undefined): number {
  return (fund?.cagr_10y ?? 0) - (fund?.ter ?? 0) / 100;
}

function grow(rate: number, year: number): number {
  return CAPITAL * (1 + rate) ** year;
}

function FundStat({ fund }: { fund: FundRow }) {
  const grossFinal = grow(fund.cagr_10y ?? 0, YEARS);
  const netFinal = grow(netRate(fund), YEARS);
  return (
    <Typography variant="body2" color="text.secondary">
      <b>{fund.ticker}</b> — growth {formatPercent(fund.cagr_10y)}/yr, TER {fund.ter ?? "n/a"}% →{" "}
      {formatMoney(netFinal)} net after {YEARS}y (fees cost {formatMoney(grossFinal - netFinal)})
    </Typography>
  );
}

// Compare two funds by growth rate (CAGR) and TER: plot each fund's net-of-fees
// growth of $10,000 over 20 years, so the fund that compounds more after fees wins.
export function FundComparisonCard({ funds }: { funds: FundRow[] }) {
  const [left, setLeft] = useState<string>("");
  const [right, setRight] = useState<string>("");

  const fundA = funds.find((fund) => fund.ticker === left);
  const fundB = funds.find((fund) => fund.ticker === right);
  const bothChosen = fundA !== undefined && fundB !== undefined;

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
            Compare two funds (growth vs TER)
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
          <Typography color="text.secondary">
            Pick two funds to compare their growth rate and TER on $10,000.
          </Typography>
        ) : (
          <>
            <LineChart
              height={300}
              xAxis={[{ data: HORIZON, label: "years" }]}
              yAxis={[{ valueFormatter: (value: number | null) => formatMoneyCompact(value) }]}
              series={[
                {
                  data: HORIZON.map((year) => grow(netRate(fundA), year)),
                  label: `${fundA.ticker} (net)`,
                  showMark: false,
                },
                {
                  data: HORIZON.map((year) => grow(netRate(fundB), year)),
                  label: `${fundB.ticker} (net)`,
                  showMark: false,
                },
              ]}
            />
            <Stack spacing={0.5} sx={{ mt: 1 }}>
              <FundStat fund={fundA} />
              <FundStat fund={fundB} />
            </Stack>
          </>
        )}
      </CardContent>
    </Card>
  );
}
