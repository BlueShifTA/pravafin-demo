"use client";

import { Box, Button, Card, CardContent, Typography } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef, GridRowSelectionModel } from "@mui/x-data-grid";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { CandleChart } from "@/components/market/CandleChart";
import { CompareDialog } from "@/components/market/CompareDialog";
import {
  useCandlesApiMarketCandlesTickerGet,
  useScreenerApiMarketScreenerGet,
} from "@/lib/generated/endpoints";

const COLUMNS: GridColDef[] = [
  { field: "magic_rank", headerName: "#", width: 70 },
  { field: "ticker", headerName: "Ticker", width: 100 },
  { field: "name", headerName: "Name", flex: 1 },
  { field: "sector", headerName: "Sector", width: 160 },
  {
    field: "earnings_yield",
    headerName: "Earnings yield",
    width: 130,
    valueFormatter: (value: number) => `${(value * 100).toFixed(1)}%`,
  },
  {
    field: "roic",
    headerName: "ROIC",
    width: 110,
    valueFormatter: (value: number) => `${(value * 100).toFixed(0)}%`,
  },
  { field: "pe_trailing", headerName: "P/E", width: 90 },
];

export default function SatellitePage() {
  const screenerQuery = useScreenerApiMarketScreenerGet({ limit: 200 });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];
  const isLoading = screenerQuery.isLoading;
  const [selection, setSelection] = useState<string[]>([]);
  const [chartTicker, setChartTicker] = useState<string | null>(null);
  const [compareOpen, setCompareOpen] = useState(false);

  const barsQuery = useCandlesApiMarketCandlesTickerGet(
    chartTicker ?? "",
    { days: 365 },
    { query: { enabled: chartTicker !== null } }
  );
  const bars = barsQuery.data?.status === 200 ? barsQuery.data.data : null;

  const onSelection = (model: GridRowSelectionModel) => {
    const ids = [...(model.ids ?? [])].map(String);
    setSelection(ids.slice(0, 4));
    if (ids.length === 1) setChartTicker(ids[0]);
  };

  return (
    <PageShell
      title="Satellite screener"
      description="Magic formula computed on the fly (EY = EBIT/EV, ROIC = EBIT/(NWC+PPE)). Select 2–4 rows to compare."
    >
      <Box sx={{ display: "grid", gap: 2 }}>
        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Screener
              </Typography>
              <Button
                variant="contained"
                disabled={selection.length < 2}
                onClick={() => setCompareOpen(true)}
              >
                Compare selected ({selection.length})
              </Button>
            </Box>
            <DataGrid
              rows={screener}
              columns={COLUMNS}
              getRowId={(row) => row.ticker}
              loading={isLoading}
              checkboxSelection
              onRowSelectionModelChange={onSelection}
              density="compact"
              sx={{ height: 480 }}
            />
          </CardContent>
        </Card>
        {chartTicker && bars && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                {chartTicker} — daily candles (1y)
              </Typography>
              <CandleChart bars={bars} />
            </CardContent>
          </Card>
        )}
      </Box>
      <CompareDialog tickers={selection} open={compareOpen} onClose={() => setCompareOpen(false)} />
    </PageShell>
  );
}
