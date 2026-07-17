"use client";

import {
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { BarChart } from "@mui/x-charts";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import {
  useFundsApiMarketFundsGet,
  useTerDragApiMarketTerDragGet,
} from "@/lib/generated/endpoints";

const currency = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export default function CorePage() {
  const fundsQuery = useFundsApiMarketFundsGet();
  const funds = fundsQuery.data?.status === 200 ? fundsQuery.data.data : [];
  const [selected, setSelected] = useState<string | null>(null);
  const dragQuery = useTerDragApiMarketTerDragGet(
    { fund: selected ?? "", capital: 10_000, years: 20 },
    { query: { enabled: selected !== null } }
  );
  const drag = dragQuery.data?.status === 200 ? dragQuery.data.data : null;

  return (
    <PageShell
      title="Core sleeve — fund comparison"
      description="Click a fund to simulate 20-year TER drag on $10,000."
    >
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card variant="outlined">
            <CardContent>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Ticker</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell align="right">TER %</TableCell>
                    <TableCell align="right">10y CAGR</TableCell>
                    <TableCell align="right">Fund size</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {funds.map((fund) => (
                    <TableRow
                      key={fund.ticker}
                      hover
                      selected={selected === fund.ticker}
                      onClick={() => setSelected(fund.ticker)}
                      sx={{ cursor: "pointer" }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>{fund.ticker}</TableCell>
                      <TableCell>{fund.name}</TableCell>
                      <TableCell align="right">{fund.ter ?? "n/a"}</TableCell>
                      <TableCell align="right">
                        {fund.cagr_10y != null ? `${(fund.cagr_10y * 100).toFixed(1)}%` : "n/a"}
                      </TableCell>
                      <TableCell align="right">
                        {fund.fund_size != null ? `$${currency.format(fund.fund_size)}` : "n/a"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 5 }}>
          {drag && (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {drag.fund_ticker}: TER drag over {drag.years}y
                </Typography>
                <BarChart
                  height={280}
                  xAxis={[{ data: ["gross", "net of TER"], scaleType: "band" }]}
                  series={[{ data: [drag.gross_value, drag.net_value] }]}
                />
                <Typography color="text.secondary">
                  {drag.ter}% TER costs ${currency.format(drag.drag)} on $
                  {currency.format(drag.capital)} at {(drag.cagr_10y * 100).toFixed(1)}% CAGR.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </PageShell>
  );
}
