export const appTokens = {
  brand: {
    primary: "#1d6ef2",
    primaryStrong: "#0f4fc2",
    secondary: "#0d9a6f",
    accent: "#f59e0b",
  },
  status: {
    success: "#1f9d61",
    warning: "#b76e00",
    error: "#b42318",
    info: "#155eef",
  },
  surface: {
    canvas: "#f4f7fb",
    card: "#ffffff",
    muted: "#eef3f9",
  },
  border: {
    subtle: "#d7e2ee",
    strong: "#9fb1c7",
  },
  text: {
    primary: "#0f172a",
    secondary: "#475467",
    muted: "#667085",
  },
  interaction: {
    hover: "#e7f0ff",
    pressed: "#d7e8ff",
    disabled: "#cbd5e1",
  },
  typography: {
    fontFamily:
      '"IBM Plex Sans", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
    monoFamily: '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  },
} as const;

export type AppTokens = typeof appTokens;
