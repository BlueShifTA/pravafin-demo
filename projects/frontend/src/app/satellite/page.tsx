"use client";

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PsychologyIcon from "@mui/icons-material/Psychology";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef, GridRowSelectionModel } from "@mui/x-data-grid";
import { useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { Spinner } from "@/components/ui/feedback/Spinner";
import { CandleChartCard } from "@/components/market/CandleChartCard";
import { CompareDialog } from "@/components/market/CompareDialog";
import { FinancialsPanel } from "@/components/market/FinancialsPanel";
import { StockAnalysisDialog } from "@/components/market/StockAnalysisDialog";
import { formatNumber, formatPercent } from "@/lib/format";
import {
  useFinancialsApiMarketFinancialsTickerGet,
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

  const financialsQuery = useFinancialsApiMarketFinancialsTickerGet(chartTicker ?? "", {
    query: { enabled: chartTicker !== null },
  });
  const financials = financialsQuery.data?.status === 200 ? financialsQuery.data.data : null;

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
        <Tooltip title={`Use AI to get detailed information on ${params.row.ticker}`}>
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
      description="Greenblatt Magic Formula ranking. Select 2–4 rows to compare."
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
              <Tooltip title="Select 2–4 rows to compare">
                <span>
                  <Button
                    variant="contained"
                    disabled={selection.length < 2}
                    onClick={() => setCompareOpen(true)}
                  >
                    Compare selected ({selection.length})
                  </Button>
                </span>
              </Tooltip>
            </Box>
            <DataGrid
              rows={rows}
              columns={columns}
              getRowId={(row) => row.ticker}
              loading={isLoading}
              checkboxSelection
              onRowSelectionModelChange={onSelection}
              density="compact"
              initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
              pageSizeOptions={[10, 25, 50, 100]}
              sx={{ height: 480 }}
            />
          </CardContent>
        </Card>
        <CandleChartCard ticker={chartTicker} />
        {chartTicker && financialsQuery.isLoading && (
          <Card variant="outlined">
            <CardContent sx={{ display: "flex", justifyContent: "center", py: 6 }}>
              <Spinner size={32} />
            </CardContent>
          </Card>
        )}
        {chartTicker && financials && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                {chartTicker} — financials
              </Typography>
              <FinancialsPanel series={financials} />
            </CardContent>
          </Card>
        )}
        <Accordion variant="outlined" disableGutters>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Methodology — the Magic Formula
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The Magic Formula (Greenblatt, 2006) ranks each equity along two independent
              dimensions — valuation and capital efficiency — and combines the ranks additively.
              Every security is assigned an ordinal rank for its earnings yield (EY) and a second
              ordinal rank for its return on invested capital (ROIC), each ordered so that higher
              values receive lower (better) ranks. The two ranks are summed to yield the composite
              score R = rank(EY) + rank(ROIC), which is then sorted in ascending order. A low
              composite score identifies a profitable business available at a low price. All ranks
              are recomputed on every request from the ingested fundamentals; no derived value is
              persisted.
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Quantity</TableCell>
                  <TableCell>Definition</TableCell>
                  <TableCell>Formula</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>EY</TableCell>
                  <TableCell>Earnings yield</TableCell>
                  <TableCell>
                    Operating profit per unit of enterprise cost; measures cheapness.
                  </TableCell>
                  <TableCell>EBIT / EV</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ROIC</TableCell>
                  <TableCell>Return on invested capital</TableCell>
                  <TableCell>
                    Operating profit per unit of capital employed; measures quality.
                  </TableCell>
                  <TableCell>EBIT / (NWC + PPE)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>EBIT</TableCell>
                  <TableCell>Earnings before interest and taxes</TableCell>
                  <TableCell>Operating profit before financing and tax effects.</TableCell>
                  <TableCell>—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>EV</TableCell>
                  <TableCell>Enterprise value</TableCell>
                  <TableCell>Total cost to acquire the business, net of cash.</TableCell>
                  <TableCell>Market cap + net debt</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>NWC</TableCell>
                  <TableCell>Net working capital</TableCell>
                  <TableCell>Short-term capital tied up in operations.</TableCell>
                  <TableCell>Current assets − current liabilities</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>PPE</TableCell>
                  <TableCell>Property, plant & equipment</TableCell>
                  <TableCell>Net tangible fixed assets.</TableCell>
                  <TableCell>—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>R</TableCell>
                  <TableCell>Composite rank</TableCell>
                  <TableCell>
                    Sum of the two ordinal ranks; sorted ascending, lower is better.
                  </TableCell>
                  <TableCell>rank(EY) + rank(ROIC)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <Chip label="Rank ≤ 10 — strong candidate" size="small" color="success" />
              <Chip label="Rank ≤ 20 — worth a look" size="small" color="primary" />
            </Stack>
          </AccordionDetails>
        </Accordion>
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
