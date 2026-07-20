"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";

type PortfolioContextValue = {
  portfolioId: number | null;
  setPortfolioId: (id: number | null) => void;
};

const PortfolioContext = createContext<PortfolioContextValue | null>(null);

export function PortfolioProvider({
  children,
  initialPortfolioId = null,
}: PropsWithChildren<{ initialPortfolioId?: number | null }>) {
  // selection is intentionally ephemeral — every fresh visit starts with no
  // portfolio selected, so we do not restore it from storage. initialPortfolioId
  // is a test seam; production mounts this propless.
  const [portfolioId, setPortfolioId] = useState<number | null>(initialPortfolioId);

  const value = useMemo<PortfolioContextValue>(
    () => ({ portfolioId, setPortfolioId }),
    [portfolioId]
  );

  return <PortfolioContext.Provider value={value}>{children}</PortfolioContext.Provider>;
}

export function usePortfolio(): PortfolioContextValue {
  const context = useContext(PortfolioContext);
  if (!context) throw new Error("usePortfolio requires PortfolioProvider");
  return context;
}
