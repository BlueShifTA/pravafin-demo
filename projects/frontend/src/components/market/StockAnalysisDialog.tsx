"use client";

import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useEffect } from "react";

import { useAnalyzeStockApiAnalysisStockPost } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

type StockAnalysisDialogProps = {
  ticker: string | null;
  open: boolean;
  onClose: () => void;
};

// magic-formula tier → chip color, ported from pravafin
const MATCH_COLOR: Record<string, "success" | "primary" | "warning" | "error" | "default"> = {
  Excellent: "success",
  Good: "primary",
  Fair: "warning",
  Poor: "error",
  Unrated: "default",
};

export function StockAnalysisDialog({ ticker, open, onClose }: StockAnalysisDialogProps) {
  const { portfolioId } = usePortfolio();
  const analyze = useAnalyzeStockApiAnalysisStockPost();
  const fullScreen = useMediaQuery(useTheme().breakpoints.down("md"));

  // fire once per open — mutation trigger, not data fetching
  useEffect(() => {
    if (open && ticker !== null && portfolioId !== null) {
      analyze.mutate({ data: { ticker, portfolio_id: portfolioId } });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, ticker]);

  const result = analyze.data?.status === 200 ? analyze.data.data : null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth fullScreen={fullScreen}>
      <DialogTitle sx={{ fontWeight: 700 }}>AI analysis: {ticker}</DialogTitle>
      <DialogContent>
        {portfolioId === null && (
          <Alert severity="info">
            Select a portfolio first — analyses are audited per portfolio.
          </Alert>
        )}
        {analyze.isPending && (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 4 }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Analyzing {ticker} with AI...</Typography>
          </Box>
        )}
        {analyze.isError && (
          <Stack spacing={1}>
            <Alert severity="error">{String(analyze.error)}</Alert>
            <Button
              onClick={() =>
                ticker !== null &&
                portfolioId !== null &&
                analyze.mutate({ data: { ticker, portfolio_id: portfolioId } })
              }
            >
              Retry
            </Button>
          </Stack>
        )}
        {analyze.data && analyze.data.status !== 200 && (
          <Alert severity="error">{JSON.stringify(analyze.data.data)}</Alert>
        )}
        {result && (
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                label={`Magic formula: ${result.magic_formula_match}`}
                color={MATCH_COLOR[result.magic_formula_match] ?? "default"}
                size="small"
              />
              {result.rank !== null && (
                <Chip label={`Rank #${result.rank}`} size="small" variant="outlined" />
              )}
            </Stack>
            <Box sx={{ borderLeft: 3, borderColor: "primary.main", pl: 2 }}>
              <Typography>{result.summary}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                Strengths
              </Typography>
              <List dense>
                {result.strengths.map((item) => (
                  <ListItem key={item} disableGutters>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleOutlinedIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={item} />
                  </ListItem>
                ))}
              </List>
            </Box>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                Weaknesses
              </Typography>
              <List dense>
                {result.weaknesses.map((item) => (
                  <ListItem key={item} disableGutters>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <WarningAmberIcon color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={item} />
                  </ListItem>
                ))}
              </List>
            </Box>
            {result.caveats.length > 0 && (
              <Alert severity="warning">{result.caveats.join(" · ")}</Alert>
            )}
          </Stack>
        )}
      </DialogContent>
    </Dialog>
  );
}
