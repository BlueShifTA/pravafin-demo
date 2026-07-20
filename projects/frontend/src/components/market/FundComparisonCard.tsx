"use client";

import {
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { LineChart } from "@mui/x-charts";

import type { FundRow } from "@/lib/generated/models";
import { formatMoney, formatPercent, moneyAxis } from "@/lib/format";

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

function feeStats(fund: FundRow) {
  const gross = grow(fund.cagr_10y ?? 0, YEARS);
  const net = grow(netRate(fund), YEARS);
  const fees = gross - net;
  return { net, fees, feesPct: gross > 0 ? fees / gross : 0 };
}

// Compare two funds by growth rate (CAGR) and TER: plot each fund's net-of-fees
// growth of $10,000 over 20 years, so the fund that compounds more after fees
// wins. The two funds are picked in the table above (selectedTickers: [A, B]).
export function FundComparisonCard({
  funds,
  selectedTickers,
}: {
  funds: FundRow[];
  selectedTickers: string[];
}) {
  const [left, right] = selectedTickers;
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
          {bothChosen && (
            <Typography variant="body2" color="text.secondary">
              {fundA.ticker} vs {fundB.ticker}
            </Typography>
          )}
        </Box>
        {!bothChosen ? (
          <Typography color="text.secondary">
            Select two funds in the table above to compare their growth rate and TER on $10,000.
          </Typography>
        ) : (
          <>
            <LineChart
              height={300}
              xAxis={[{ data: HORIZON, label: "years" }]}
              yAxis={[
                moneyAxis(Math.max(grow(netRate(fundA), YEARS), grow(netRate(fundB), YEARS))),
              ]}
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
            <Table size="small" sx={{ mt: 1 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Fund</TableCell>
                  <TableCell align="right">Growth / yr</TableCell>
                  <TableCell align="right">TER</TableCell>
                  <TableCell align="right">Net after {YEARS}y</TableCell>
                  <TableCell align="right">Fees cost</TableCell>
                  <TableCell align="right">Fees %</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[fundA, fundB].map((fund) => {
                  const stats = feeStats(fund);
                  return (
                    <TableRow key={fund.ticker}>
                      <TableCell sx={{ fontWeight: 600 }}>{fund.ticker}</TableCell>
                      <TableCell align="right">{formatPercent(fund.cagr_10y)}</TableCell>
                      <TableCell align="right">{fund.ter ?? "n/a"}%</TableCell>
                      <TableCell align="right">{formatMoney(stats.net)}</TableCell>
                      <TableCell align="right">{formatMoney(stats.fees)}</TableCell>
                      <TableCell align="right">{formatPercent(stats.feesPct)}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </>
        )}
      </CardContent>
    </Card>
  );
}
