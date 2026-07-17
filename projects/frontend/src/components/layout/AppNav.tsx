"use client";

import {
  AppBar,
  Box,
  Chip,
  Drawer,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItemButton,
  ListItemText,
  MenuItem,
  Select,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import type { PropsWithChildren } from "react";

import { useListPortfoliosApiPortfoliosGet } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

const DRAWER_WIDTH = 200;

const NAV_ITEMS = [
  { label: "Main", href: "/" },
  { label: "Core", href: "/core" },
  { label: "Satellite", href: "/satellite" },
  { label: "Indicators", href: "/indicators" },
  { label: "Ingestion", href: "/ingestion" },
  { label: "New portfolio", href: "/wizard" },
] as const;

export function AppNav({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const { portfolioId, setPortfolioId } = usePortfolio();
  const portfoliosQuery = useListPortfoliosApiPortfoliosGet();
  const portfolios = portfoliosQuery.data?.status === 200 ? portfoliosQuery.data.data : [];
  const [copilotOpen, setCopilotOpen] = useState(false);

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            CoreSat
          </Typography>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel id="portfolio-select">Portfolio</InputLabel>
            <Select
              labelId="portfolio-select"
              label="Portfolio"
              value={portfolioId ?? ""}
              onChange={(event) => setPortfolioId(Number(event.target.value))}
            >
              {portfolios.map((portfolio) => (
                <MenuItem key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Tooltip title="Copilot — coming in V2 (LangGraph agent)">
            <span>
              <IconButton
                aria-label="copilot"
                onClick={() => setCopilotOpen(true)}
                sx={{ color: "inherit" }}
              >
                🤖
              </IconButton>
            </span>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <List>
          {NAV_ITEMS.map((item) => (
            <ListItemButton
              key={item.href}
              component={Link}
              href={item.href}
              selected={pathname === item.href}
            >
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Drawer anchor="right" open={copilotOpen} onClose={() => setCopilotOpen(false)}>
        <Box sx={{ width: 320, p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Copilot
          </Typography>
          <Chip label="V2" size="small" color="warning" sx={{ my: 1 }} />
          <Typography color="text.secondary">
            Per-portfolio chat with grounded answers (LangGraph agent: scope guard → orchestrator →
            RAG / SQL tools → synthesiser → grounding validator). Ships in V2 — the UI slot is
            reserved so the product shape is complete.
          </Typography>
        </Box>
      </Drawer>
      <Box component="section" sx={{ flexGrow: 1, ml: `${DRAWER_WIDTH}px`, mt: 8 }}>
        {children}
      </Box>
    </Box>
  );
}
