"use client";

import { Box, Container, Stack, Typography } from "@mui/material";
import type { PropsWithChildren, ReactNode } from "react";

type PageShellProps = PropsWithChildren<{
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}>;

export function PageShell({ eyebrow, title, description, actions, children }: PageShellProps) {
  return (
    <main className="min-h-screen py-10 sm:py-14">
      <Container maxWidth="lg">
        <Stack spacing={4}>
          <Box
            sx={{
              borderRadius: 4,
              border: "1px solid var(--color-border-subtle)",
              background:
                "linear-gradient(160deg, var(--color-surface-card) 0%, var(--color-surface-muted) 100%)",
              p: { xs: 3, sm: 4 },
              boxShadow: "0 18px 32px rgba(15, 23, 42, 0.08)",
            }}
          >
            {eyebrow ? (
              <Typography
                variant="overline"
                sx={{
                  color: "var(--color-brand-primary-strong)",
                  letterSpacing: "0.18em",
                  fontWeight: 700,
                }}
              >
                {eyebrow}
              </Typography>
            ) : null}
            <Typography component="h1" variant="h3" sx={{ mt: eyebrow ? 1.25 : 0 }}>
              {title}
            </Typography>
            {description ? (
              <Typography variant="body1" color="text.secondary" sx={{ mt: 1.5, maxWidth: 840 }}>
                {description}
              </Typography>
            ) : null}
            {actions ? (
              <Box className="mt-4 flex flex-wrap gap-2 sm:gap-3" sx={{ mt: 3 }}>
                {actions}
              </Box>
            ) : null}
          </Box>

          <Stack spacing={3}>{children}</Stack>
        </Stack>
      </Container>
    </main>
  );
}
