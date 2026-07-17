"use client";

import {
  AppBar,
  Box,
  Chip,
  Divider,
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
  useMediaQuery,
  useTheme,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import MenuIcon from "@mui/icons-material/Menu";
import SmartToyIcon from "@mui/icons-material/SmartToy";
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
] as const;

export function AppNav({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const { portfolioId, setPortfolioId } = usePortfolio();
  const portfoliosQuery = useListPortfoliosApiPortfoliosGet();
  const portfolios = portfoliosQuery.data?.status === 200 ? portfoliosQuery.data.data : [];
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [desktopNavOpen, setDesktopNavOpen] = useState(true);
  const isDesktop = useMediaQuery(useTheme().breakpoints.up("md"));

  const navList = (
    <List>
      {NAV_ITEMS.map((item) => (
        <ListItemButton
          key={item.href}
          component={Link}
          href={item.href}
          selected={pathname === item.href}
          onClick={() => setMobileNavOpen(false)}
        >
          <ListItemText primary={item.label} />
        </ListItemButton>
      ))}
    </List>
  );

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ gap: { xs: 1, sm: 2 } }}>
          <IconButton
            aria-label="toggle navigation"
            onClick={() =>
              isDesktop ? setDesktopNavOpen((open) => !open) : setMobileNavOpen((open) => !open)
            }
            sx={{ color: "inherit" }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            CoreSat
          </Typography>
          <FormControl size="small" sx={{ minWidth: { xs: 130, sm: 180 } }}>
            <InputLabel id="portfolio-select">Portfolio</InputLabel>
            <Select
              labelId="portfolio-select"
              label="Portfolio"
              value={portfolioId ?? ""}
              onChange={(event) => {
                if (typeof event.target.value === "number") {
                  setPortfolioId(event.target.value);
                }
              }}
            >
              {portfolios.map((portfolio) => (
                <MenuItem key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </MenuItem>
              ))}
              <Divider />
              <MenuItem component={Link} href="/wizard">
                <AddIcon fontSize="small" sx={{ mr: 1 }} />
                New portfolio
              </MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Copilot — coming in V2 (LangGraph agent)">
            <span>
              <IconButton
                aria-label="copilot"
                onClick={() => setCopilotOpen(true)}
                sx={{ color: "inherit" }}
              >
                <SmartToyIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="persistent"
        open={desktopNavOpen}
        sx={{
          width: desktopNavOpen ? DRAWER_WIDTH : 0,
          display: { xs: "none", md: "block" },
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        {navList}
      </Drawer>
      <Drawer
        variant="temporary"
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        {navList}
      </Drawer>
      <Drawer anchor="right" open={copilotOpen} onClose={() => setCopilotOpen(false)}>
        <Box sx={{ width: { xs: "85vw", sm: 320 }, p: 3 }}>
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
      <Box
        component="section"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          ml: { xs: 0, md: desktopNavOpen ? `${DRAWER_WIDTH}px` : 0 },
          mt: 8,
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
