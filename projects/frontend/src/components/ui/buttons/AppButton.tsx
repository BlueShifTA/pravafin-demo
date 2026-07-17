"use client";

import { Button } from "@mui/material";
import type { ButtonProps } from "@mui/material";

export type AppButtonProps = ButtonProps;

export function AppButton({
  variant = "contained",
  color = "primary",
  size = "medium",
  ...props
}: AppButtonProps) {
  return <Button color={color} size={size} variant={variant} {...props} />;
}
