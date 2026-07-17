"use client";

import { Box, CircularProgress } from "@mui/material";
import type { ButtonProps } from "@mui/material";
import type { ReactNode } from "react";

import { AppButton } from "@/components/ui/buttons/AppButton";

export type ButtonWithSpinnerProps = ButtonProps & {
  isLoading?: boolean;
  spinnerSize?: number;
  children: ReactNode;
};

export function ButtonWithSpinner({
  isLoading = false,
  spinnerSize = 18,
  children,
  disabled,
  endIcon,
  ...props
}: ButtonWithSpinnerProps) {
  return (
    <AppButton
      {...props}
      disabled={disabled || isLoading}
      endIcon={isLoading ? undefined : endIcon}
    >
      <Box sx={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
        <Box sx={isLoading ? { visibility: "hidden" } : undefined}>{children}</Box>
        {isLoading ? (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress color="inherit" size={spinnerSize} thickness={5} />
          </Box>
        ) : null}
      </Box>
    </AppButton>
  );
}
