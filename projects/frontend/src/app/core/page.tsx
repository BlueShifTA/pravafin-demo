"use client";

import {
  Box,
  Card,
  CardContent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { LineChart } from "@mui/x-charts";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { Spinner } from "@/components/ui/feedback/Spinner";
import { formatMoney, formatNumber, formatPercent } from "@/lib/format";
import {
  useFundsApiMarketFundsGet,
  useTerDragApiMarketTerDragGet,
} from "@/lib/generated/endpoints";

// 8 rows at size="small" density; the rest scroll within the container
const VISIBLE_ROWS = 8;
const ROW_HEIGHT_PX = 37;

export default function CorePage() {
  const fundsQuery = useFundsApiMarketFundsGet();
  const funds = fundsQuery.data?.status === 200 ? fundsQuery.data.data : [];
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const dragQuery = useTerDragApiMarketTerDragGet(
    { fund: selected ?? "", capital: 10_000, years: 20 },
    { query: { enabled: selected !== null } }
  );
  const drag = dragQuery.data?.status === 200 ? dragQuery.data.data : null;

  const query = search.trim().toLowerCase();
  const visibleFunds =
    query === ""
      ? funds
      : funds.filter(
          (fund) =>
            fund.ticker.toLowerCase().includes(query) ||
            (fund.name ?? "").toLowerCase().includes(query)
        );

  const rippedPercent = drag && drag.gross_value > 0 ? (drag.drag / drag.gross_value) * 100 : null;

  return (
    <PageShell
      title="Core sleeve — fund comparison"
      description="Click a fund to simulate 20-year TER drag on $10,000."
    >
      <Stack spacing={2}>
        <Card variant="outlined">
          <CardContent>
            <TextField
              size="small"
              fullWidth
              label="Search funds"
              placeholder="Ticker or name"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              sx={{ mb: 1.5 }}
            />
            {fundsQuery.isLoading && (
              <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                <Spinner size={32} />
              </Box>
            )}
            <TableContainer sx={{ maxHeight: ROW_HEIGHT_PX * (VISIBLE_ROWS + 1) }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Ticker</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Sector</TableCell>
                    <TableCell align="right">Holdings</TableCell>
                    <TableCell align="right">TER %</TableCell>
                    <TableCell align="right">10y CAGR</TableCell>
                    <TableCell align="right">Fund size</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {visibleFunds.map((fund) => (
                    <TableRow
                      key={fund.ticker}
                      hover
                      selected={selected === fund.ticker}
                      onClick={() => setSelected(fund.ticker)}
                      sx={{ cursor: "pointer" }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>{fund.ticker}</TableCell>
                      <TableCell>{fund.name}</TableCell>
                      <TableCell>{fund.category ?? "n/a"}</TableCell>
                      <TableCell align="right">{formatNumber(fund.holdings_count)}</TableCell>
                      <TableCell align="right">{fund.ter ?? "n/a"}</TableCell>
                      <TableCell align="right">{formatPercent(fund.cagr_10y)}</TableCell>
                      <TableCell align="right">
                        {formatMoney(fund.fund_size, fund.currency ?? "USD")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
        {dragQuery.isLoading && (
          <Card variant="outlined">
            <CardContent sx={{ display: "flex", justifyContent: "center", py: 6 }}>
              <Spinner size={32} />
            </CardContent>
          </Card>
        )}
        {drag && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {drag.fund_ticker}: {formatMoney(drag.capital)} over {drag.years} years
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Growth at {formatPercent(drag.cagr_10y)} CAGR, gross versus net after the {drag.ter}
                % TER.
              </Typography>
              <LineChart
                height={320}
                xAxis={[{ data: drag.series.map((point) => point.year), label: "year" }]}
                series={[
                  {
                    data: drag.series.map((point) => point.gross_value),
                    label: "Gross growth",
                    color: "#1976d2",
                    showMark: false,
                  },
                  {
                    data: drag.series.map((point) => point.net_value),
                    label: "Net after TER",
                    color: "#ff9800",
                    showMark: false,
                    area: true,
                  },
                ]}
              />
              <Box sx={{ mt: 1 }}>
                <Typography color="text.secondary">
                  After {drag.years} years: {formatMoney(drag.gross_value)} gross versus{" "}
                  {formatMoney(drag.net_value)} net — the TER rips out {formatMoney(drag.drag)}
                  {rippedPercent !== null &&
                    ` (${formatPercent(rippedPercent / 100)} of the final gross value)`}
                  .
                </Typography>
              </Box>
            </CardContent>
          </Card>
        )}
      </Stack>
    </PageShell>
  );
}
