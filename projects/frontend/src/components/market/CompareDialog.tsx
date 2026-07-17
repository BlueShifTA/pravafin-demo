"use client";

import {
  Alert,
  Box,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect } from "react";

import { useCompareApiComparePost } from "@/lib/generated/endpoints";
import { usePortfolio } from "@/lib/portfolio-context";

type CompareDialogProps = {
  tickers: string[];
  open: boolean;
  onClose: () => void;
};

export function CompareDialog({ tickers, open, onClose }: CompareDialogProps) {
  const { portfolioId } = usePortfolio();
  const compare = useCompareApiComparePost();

  // fire once per open — mutation trigger, not data fetching
  useEffect(() => {
    if (open && tickers.length >= 2 && portfolioId !== null) {
      compare.mutate({ data: { tickers, portfolio_id: portfolioId } });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>Compare: {tickers.join(" vs ")}</DialogTitle>
      <DialogContent>
        {portfolioId === null && (
          <Alert severity="info">
            Select a portfolio first — comparisons are audited per portfolio.
          </Alert>
        )}
        {compare.isPending && (
          <Typography color="text.secondary">
            Asking the local model (grounded on ingested fundamentals)…
          </Typography>
        )}
        {compare.isError && <Alert severity="error">{String(compare.error)}</Alert>}
        {compare.data && compare.data.status !== 200 && (
          <Alert severity="error">{JSON.stringify(compare.data.data)}</Alert>
        )}
        {compare.data && compare.data.status === 200 && (
          <Stack spacing={2}>
            <Stack direction="row" spacing={1}>
              {tickers.map((ticker) => (
                <Chip key={ticker} label={ticker} variant="outlined" color="primary" />
              ))}
            </Stack>
            <Box sx={{ borderLeft: 3, borderColor: "primary.main", pl: 2 }}>
              <Typography>{compare.data.data.summary}</Typography>
            </Box>
            <Divider />
            {compare.data.data.per_criterion.map((verdict) => (
              <Stack key={verdict.criterion} direction="row" spacing={2} alignItems="baseline">
                <Chip label={verdict.criterion} size="small" />
                <Typography sx={{ fontWeight: 600, minWidth: 64 }}>{verdict.winner}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {verdict.reasoning}
                </Typography>
              </Stack>
            ))}
            {compare.data.data.caveats.length > 0 && (
              <Alert severity="warning">{compare.data.data.caveats.join(" · ")}</Alert>
            )}
            <Alert severity="info">
              AI-generated comparison from a local model ({compare.data.data.model}) — every number
              checked against injected facts. Not investment advice.
            </Alert>
          </Stack>
        )}
      </DialogContent>
    </Dialog>
  );
}
