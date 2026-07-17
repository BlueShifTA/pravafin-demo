"use client";

import { Paper, Stack, Typography } from "@mui/material";
import type { PropsWithChildren } from "react";

type SectionProps = PropsWithChildren<{
  title: string;
  description?: string;
}>;

export function Section({ title, description, children }: SectionProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 3,
        border: "1px solid var(--color-border-subtle)",
        backgroundColor: "var(--color-surface-card)",
        p: 2.5,
      }}
    >
      <Stack spacing={1.5}>
        <div>
          <Typography variant="subtitle1">{title}</Typography>
          {description ? (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {description}
            </Typography>
          ) : null}
        </div>
        {children}
      </Stack>
    </Paper>
  );
}
