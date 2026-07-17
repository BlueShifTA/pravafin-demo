"use client";

import { CircularProgress } from "@mui/material";
import type { CircularProgressProps } from "@mui/material";

export function Spinner(props: CircularProgressProps) {
  return <CircularProgress size={18} thickness={5} {...props} />;
}
