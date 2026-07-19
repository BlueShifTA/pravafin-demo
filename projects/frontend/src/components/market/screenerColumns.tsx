import { Chip } from "@mui/material";
import type { GridColDef } from "@mui/x-data-grid";

import { formatNumber, formatPercent } from "@/lib/format";

// Rank tiers ported from pravafin's screening grid.
export function rankColor(rank: number): "success" | "primary" | "default" {
  if (rank <= 10) return "success";
  if (rank <= 20) return "primary";
  return "default";
}

// The magic-formula columns shared by the satellite screener page and the
// wizard's satellite step, so both show the same table. The screener page
// appends its own AI-analyze column after these.
export const screenerColumns: GridColDef[] = [
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
];
