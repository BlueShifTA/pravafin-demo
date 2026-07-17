import { alpha, createTheme } from "@mui/material/styles";

import { appTokens } from "@/theme/tokens";

export const appTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: appTokens.brand.primary,
      dark: appTokens.brand.primaryStrong,
    },
    secondary: {
      main: appTokens.brand.secondary,
    },
    success: {
      main: appTokens.status.success,
    },
    warning: {
      main: appTokens.status.warning,
    },
    error: {
      main: appTokens.status.error,
    },
    background: {
      default: appTokens.surface.canvas,
      paper: appTokens.surface.card,
    },
    text: {
      primary: appTokens.text.primary,
      secondary: appTokens.text.secondary,
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: appTokens.typography.fontFamily,
    h3: {
      fontWeight: 700,
      letterSpacing: "-0.02em",
      fontSize: "clamp(1.75rem, 2.3vw, 2.4rem)",
    },
    body1: {
      lineHeight: 1.55,
    },
    subtitle1: {
      fontWeight: 600,
    },
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 10,
          paddingInline: 14,
        },
        containedPrimary: {
          boxShadow: "0 6px 16px rgba(29, 110, 242, 0.18)",
          "&:hover": {
            boxShadow: "0 8px 20px rgba(29, 110, 242, 0.22)",
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: alpha(appTokens.surface.card, 0.85),
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: appTokens.border.subtle,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: appTokens.border.strong,
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: appTokens.brand.primary,
            borderWidth: 1,
          },
        },
        input: {
          fontSize: "0.95rem",
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          color: appTokens.text.muted,
        },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: {
          marginLeft: 0,
          marginRight: 0,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        rounded: {
          borderRadius: 14,
        },
      },
    },
  },
});
