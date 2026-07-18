// Brand system aligned to etops.com — violet #8B48FF on lavender/white, Poppins.
export const appTokens = {
  brand: {
    primary: "#8B48FF",
    primaryStrong: "#7433E8",
    secondary: "#9E66FF",
    accent: "#F59E0B",
  },
  status: {
    success: "#16A34A",
    warning: "#D97706",
    error: "#DC2626",
    info: "#8B48FF",
  },
  surface: {
    canvas: "#F7F6FF",
    card: "#FFFFFF",
    muted: "#F0EFFD",
  },
  border: {
    subtle: "#E7E3FB",
    strong: "#C9BEF2",
  },
  text: {
    primary: "#1A1633",
    secondary: "#5B5470",
    muted: "#8B8398",
  },
  interaction: {
    hover: "#F0EFFD",
    pressed: "#E3DEFA",
    disabled: "#D8D3E6",
  },
  typography: {
    fontFamily: '"Poppins", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
    monoFamily: '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  },
} as const;

export type AppTokens = typeof appTokens;
