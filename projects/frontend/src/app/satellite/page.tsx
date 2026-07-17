"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import PsychologyIcon from "@mui/icons-material/Psychology";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef, GridRowSelectionModel } from "@mui/x-data-grid";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { CandleChart } from "@/components/market/CandleChart";
import { CompareDialog } from "@/components/market/CompareDialog";
import { StockAnalysisDialog } from "@/components/market/StockAnalysisDialog";
import { formatNumber, formatPercent } from "@/lib/format";
import {
  useCandlesApiMarketCandlesTickerGet,
  useIndicatorsApiMarketIndicatorsTickerGet,
  useScreenerApiMarketScreenerGet,
} from "@/lib/generated/endpoints";

const LIMITS = [10, 20, 30, 50, 100, 200] as const;

// rank tiers ported from pravafin's screening grid
function rankColor(rank: number): "success" | "primary" | "default" {
  if (rank <= 10) return "success";
  if (rank <= 20) return "primary";
  return "default";
}

export default function SatellitePage() {
  const [limit, setLimit] = useState<number>(200);
  const [sector, setSector] = useState<string>("all");
  const screenerQuery = useScreenerApiMarketScreenerGet({ limit });
  const screener = screenerQuery.data?.status === 200 ? screenerQuery.data.data : [];
  const sectors = [...new Set(screener.map((row) => row.sector).filter(Boolean))].sort();
  const rows = sector === "all" ? screener : screener.filter((row) => row.sector === sector);
  const isLoading = screenerQuery.isLoading;
  const [selection, setSelection] = useState<string[]>([]);
  const [chartTicker, setChartTicker] = useState<string | null>(null);
  const [compareOpen, setCompareOpen] = useState(false);
  const [analysisTicker, setAnalysisTicker] = useState<string | null>(null);

  const barsQuery = useCandlesApiMarketCandlesTickerGet(
    chartTicker ?? "",
    { days: 365 },
    { query: { enabled: chartTicker !== null } }
  );
  const bars = barsQuery.data?.status === 200 ? barsQuery.data.data : null;
  const indicatorsQuery = useIndicatorsApiMarketIndicatorsTickerGet(
    chartTicker ?? "",
    { days: 365 },
    { query: { enabled: chartTicker !== null } }
  );
  const indicators = indicatorsQuery.data?.status === 200 ? indicatorsQuery.data.data : undefined;

  const onSelection = (model: GridRowSelectionModel) => {
    const ids = [...(model.ids ?? [])].map(String);
    setSelection(ids.slice(0, 4));
    if (ids.length === 1) setChartTicker(ids[0]);
  };

  const columns: GridColDef[] = [
    {
      field: "magic_rank",
      headerName: "#",
      width: 80,
      renderCell: (params) => (
        <Chip label={params.value} size="small" color={rankColor(Number(params.value))} />
      ),
    },
    { field: "ticker", headerName: "Ticker", width: 100 },
    { field: "name", headerName: "Name", flex: 1 },
    { field: "sector", headerName: "Sector", width: 160 },
    {
      field: "earnings_yield",
      headerName: "Earnings yield",
      description: "EBIT / enterprise value — how much operating profit per euro paid",
      width: 130,
      valueFormatter: (value: number) => formatPercent(value),
    },
    {
      field: "roic",
      headerName: "ROIC",
      description: "EBIT / (net working capital + PPE) — how well capital compounds",
      width: 110,
      valueFormatter: (value: number) => formatPercent(value, 0),
    },
    {
      field: "pe_trailing",
      headerName: "P/E",
      width: 90,
      valueFormatter: (value: number | null) => formatNumber(value),
    },
    {
      field: "analyze",
      headerName: "AI",
      width: 70,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Tooltip title={`AI analysis of ${params.row.ticker}`}>
          <IconButton size="small" onClick={() => setAnalysisTicker(String(params.row.ticker))}>
            <PsychologyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <PageShell
      title="Satellite screener"
      description="Magic formula computed on the fly (EY = EBIT/EV, ROIC = EBIT/(NWC+PPE)). Select 2–4 rows to compare."
    >
      <Box sx={{ display: "grid", gap: 2 }}>
        <Card variant="outlined">
          <CardContent>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                mb: 1,
                gap: 2,
                flexWrap: "wrap",
              }}
            >
              <Stack
                direction="row"
                spacing={2}
                alignItems="center"
                sx={{ flexWrap: "wrap", rowGap: 1.5 }}
              >
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Screener
                </Typography>
                <FormControl size="small" sx={{ minWidth: 180 }}>
                  <InputLabel id="sector-filter">Sector</InputLabel>
                  <Select
                    labelId="sector-filter"
                    label="Sector"
                    value={sector}
                    onChange={(event) => setSector(String(event.target.value))}
                  >
                    <MenuItem value="all">All sectors</MenuItem>
                    {sectors.map((name) => (
                      <MenuItem key={name} value={name ?? ""}>
                        {name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 110 }}>
                  <InputLabel id="limit-select">Stocks</InputLabel>
                  <Select
                    labelId="limit-select"
                    label="Stocks"
                    value={limit}
                    onChange={(event) => setLimit(Number(event.target.value))}
                  >
                    {LIMITS.map((value) => (
                      <MenuItem key={value} value={value}>
                        {value}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>
              <Button
                variant="contained"
                disabled={selection.length < 2}
                onClick={() => setCompareOpen(true)}
              >
                Compare selected ({selection.length})
              </Button>
            </Box>
            <DataGrid
              rows={rows}
              columns={columns}
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
              <CandleChart bars={bars} indicators={indicators} />
            </CardContent>
          </Card>
        )}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
              How the magic formula works
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Greenblatt&apos;s magic formula ranks every stock twice — once by earnings yield
              (cheapness) and once by ROIC (quality) — then sums the two ranks. The lowest combined
              rank wins: good businesses at fair prices. Ranks here are recomputed on every request
              from ingested fundamentals.
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <Chip label="Rank ≤ 10 — strong candidate" size="small" color="success" />
              <Chip label="Rank ≤ 20 — worth a look" size="small" color="primary" />
              <Chip
                icon={<PsychologyIcon />}
                label="grounded AI analysis"
                size="small"
                variant="outlined"
              />
            </Stack>
          </CardContent>
        </Card>
      </Box>
      <CompareDialog tickers={selection} open={compareOpen} onClose={() => setCompareOpen(false)} />
      <StockAnalysisDialog
        ticker={analysisTicker}
        open={analysisTicker !== null}
        onClose={() => setAnalysisTicker(null)}
      />
    </PageShell>
  );
}
