"use client";

import { TextField } from "@mui/material";
import type { TextFieldProps } from "@mui/material";

export type AppTextFieldProps = TextFieldProps;

export function AppTextField({
  variant = "outlined",
  size = "small",
  fullWidth = true,
  ...props
}: AppTextFieldProps) {
  return <TextField fullWidth={fullWidth} size={size} variant={variant} {...props} />;
}
