"use client";

import {
  AppBar,
  Box,
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
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import MenuIcon from "@mui/icons-material/Menu";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { PropsWithChildren } from "react";

import { CopilotDrawer } from "@/components/copilot/CopilotDrawer";
import { useListPortfoliosApiPortfoliosGet } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

const DRAWER_WIDTH = 200;
// frontend-only "delete": ids the user removed from the picker. The portfolio
// still exists server-side (no delete API) — we just stop showing it here.
const HIDDEN_KEY = "coresat.hiddenPortfolios";

const NAV_ITEMS = [
  { label: "Main", href: "/" },
  { label: "ETF", href: "/core" },
  { label: "Stock", href: "/satellite" },
  // hidden for the demo — pages still exist, re-enable by uncommenting
  // { label: "Indicators", href: "/indicators" },
  // { label: "Ingestion", href: "/ingestion" },
] as const;

export function AppNav({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const { portfolioId, setPortfolioId } = usePortfolio();
  const portfoliosQuery = useListPortfoliosApiPortfoliosGet();
  const allPortfolios = portfoliosQuery.data?.status === 200 ? portfoliosQuery.data.data : [];
  const [hiddenIds, setHiddenIds] = useState<number[]>([]);
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(HIDDEN_KEY);
      if (raw) setHiddenIds(JSON.parse(raw) as number[]);
    } catch {
      /* no storage available */
    }
  }, []);
  const hidePortfolio = (id: number) => {
    setHiddenIds((prev) => {
      const next = prev.includes(id) ? prev : [...prev, id];
      try {
        window.localStorage.setItem(HIDDEN_KEY, JSON.stringify(next));
      } catch {
        /* no storage available */
      }
      return next;
    });
    if (portfolioId === id) setPortfolioId(null);
  };
  const portfolios = allPortfolios.filter((portfolio) => !hiddenIds.includes(portfolio.id));
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
            DCA planner
          </Typography>
          <FormControl size="small" sx={{ minWidth: { xs: 130, sm: 180 } }}>
            <InputLabel id="portfolio-select">Portfolio</InputLabel>
            <Select
              labelId="portfolio-select"
              label="Portfolio"
              value={portfolioId ?? ""}
              renderValue={(value) => portfolios.find((p) => p.id === value)?.name ?? ""}
              onChange={(event) => {
                if (typeof event.target.value === "number") {
                  setPortfolioId(event.target.value);
                }
              }}
            >
              {portfolios.map((portfolio) => (
                <MenuItem
                  key={portfolio.id}
                  value={portfolio.id}
                  sx={{ display: "flex", justifyContent: "space-between", gap: 1, pr: 0.5 }}
                >
                  {portfolio.name}
                  <Tooltip title="Remove from list">
                    <IconButton
                      edge="end"
                      size="small"
                      aria-label={`remove ${portfolio.name}`}
                      onClick={(event) => {
                        event.stopPropagation();
                        hidePortfolio(portfolio.id);
                      }}
                    >
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </MenuItem>
              ))}
              <Divider />
              <MenuItem component={Link} href="/wizard">
                <AddIcon fontSize="small" sx={{ mr: 1 }} />
                New portfolio
              </MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Assistant">
            <span>
              <IconButton
                aria-label="assistant"
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
      <CopilotDrawer open={copilotOpen} onClose={() => setCopilotOpen(false)} />
      {/* no margin-left: the drawer's root box already reserves its width in this flex row */}
      <Box component="section" sx={{ flexGrow: 1, minWidth: 0, mt: 8 }}>
        {children}
      </Box>
    </Box>
  );
}
