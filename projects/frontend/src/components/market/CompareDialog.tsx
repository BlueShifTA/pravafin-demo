"use client";

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
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

import { useCompareApiComparePost } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

type CompareDialogProps = {
  tickers: string[];
  open: boolean;
  onClose: () => void;
};

// section layout ported from pravafin's CompareStocksDialog
function SectionHeading({ children }: { children: string }) {
  return (
    <Typography variant="h6" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
      {children}
    </Typography>
  );
}

export function CompareDialog({ tickers, open, onClose }: CompareDialogProps) {
  const { portfolioId } = usePortfolio();
  const compare = useCompareApiComparePost();
  const fullScreen = useMediaQuery(useTheme().breakpoints.down("md"));

  // fire once per open — mutation trigger, not data fetching
  useEffect(() => {
    if (open && tickers.length >= 2 && portfolioId !== null) {
      compare.mutate({ data: { tickers, portfolio_id: portfolioId } });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const result = compare.data?.status === 200 ? compare.data.data : null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth fullScreen={fullScreen}>
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1, fontWeight: 700 }}>
        <span aria-hidden>🆚</span> AI Stock Comparison
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Comparing Stocks:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {tickers.map((ticker) => (
              <Chip key={ticker} label={ticker} color="primary" variant="outlined" />
            ))}
          </Stack>
        </Box>
        {portfolioId === null && (
          <Alert severity="info">
            Select a portfolio first — comparisons are audited per portfolio.
          </Alert>
        )}
        {compare.isPending && (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 4 }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Analyzing stocks with AI...</Typography>
          </Box>
        )}
        {compare.isError && !compare.isPending && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {String(compare.error)}
          </Alert>
        )}
        {compare.data && compare.data.status !== 200 && (
          <Alert severity="error">{JSON.stringify(compare.data.data)}</Alert>
        )}
        {result && !compare.isPending && (
          <Box>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1, fontWeight: 600 }}
            >
              <span aria-hidden>🧠</span> AI Analysis
            </Typography>

            <SectionHeading>Comparison Summary</SectionHeading>
            <Typography sx={{ lineHeight: 1.8 }}>{result.summary}</Typography>

            <SectionHeading>Pros &amp; Cons</SectionHeading>
            <Box
              sx={{
                display: "grid",
                gap: 2,
                gridTemplateColumns: { xs: "1fr", md: "repeat(auto-fit, minmax(260px, 1fr))" },
              }}
            >
              {result.per_ticker.map((assessment) => (
                <Box
                  key={assessment.ticker}
                  sx={{ border: 1, borderColor: "divider", borderRadius: 1, p: 2 }}
                >
                  <Typography sx={{ fontWeight: 600, mb: 1 }}>{assessment.ticker}</Typography>
                  <Typography variant="subtitle2" color="success.main">
                    Pros
                  </Typography>
                  <List dense>
                    {assessment.pros.map((item) => (
                      <ListItem key={item} disableGutters>
                        <ListItemIcon sx={{ minWidth: 24, color: "success.main" }}>✓</ListItemIcon>
                        <ListItemText primary={item} />
                      </ListItem>
                    ))}
                  </List>
                  <Typography variant="subtitle2" color="warning.main">
                    Cons
                  </Typography>
                  <List dense>
                    {assessment.cons.map((item) => (
                      <ListItem key={item} disableGutters>
                        <ListItemIcon sx={{ minWidth: 24, color: "warning.main" }}>⚠</ListItemIcon>
                        <ListItemText primary={item} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ))}
            </Box>

            <SectionHeading>Top Pick</SectionHeading>
            <Alert severity="success" icon="🏆">
              {result.recommendation}
            </Alert>

            <SectionHeading>Key Differentiators</SectionHeading>
            <Stack spacing={1.5}>
              {result.per_criterion.map((verdict) => (
                <Stack key={verdict.criterion} direction="row" spacing={2} alignItems="baseline">
                  <Chip label={verdict.criterion} size="small" />
                  <Typography sx={{ fontWeight: 600, minWidth: 64 }}>{verdict.winner}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {verdict.reasoning}
                  </Typography>
                </Stack>
              ))}
            </Stack>

            {result.caveats.length > 0 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                {result.caveats.join(" · ")}
              </Alert>
            )}
            <Divider sx={{ my: 2 }} />
            <Alert severity="warning">
              This comparison is AI-generated ({result.model}, every number checked against injected
              facts) and should not be considered as financial advice. Always conduct your own
              research before making investment decisions.
            </Alert>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        {compare.isError && portfolioId !== null && (
          <Button
            variant="contained"
            onClick={() => compare.mutate({ data: { tickers, portfolio_id: portfolioId } })}
          >
            Retry
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
