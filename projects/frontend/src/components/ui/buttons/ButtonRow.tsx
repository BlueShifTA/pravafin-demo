"use client";

import { Stack } from "@mui/material";
import type { PropsWithChildren } from "react";

type ButtonRowProps = PropsWithChildren<{
  compact?: boolean;
}>;

export function ButtonRow({ compact = false, children }: ButtonRowProps) {
  return (
    <Stack
      direction="row"
      flexWrap="wrap"
      gap={compact ? 1 : 1.5}
      alignItems="center"
      justifyContent="flex-start"
    >
      {children}
    </Stack>
  );
}
