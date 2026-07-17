"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";

type PortfolioContextValue = {
  portfolioId: number | null;
  setPortfolioId: (id: number | null) => void;
};

const PortfolioContext = createContext<PortfolioContextValue | null>(null);

const STORAGE_KEY = "coresat.portfolioId";

export function PortfolioProvider({ children }: PropsWithChildren) {
  const [portfolioId, setPortfolioId] = useState<number | null>(null);

  // hydrate once from localStorage (client-only value, not data fetching);
  // storage is absent in the vitest DOM — degrade to in-memory state
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) setPortfolioId(Number(stored));
    } catch {
      /* no storage available */
    }
  }, []);

  const value = useMemo<PortfolioContextValue>(
    () => ({
      portfolioId,
      setPortfolioId: (id) => {
        setPortfolioId(id);
        try {
          if (id === null) window.localStorage.removeItem(STORAGE_KEY);
          else window.localStorage.setItem(STORAGE_KEY, String(id));
        } catch {
          /* no storage available */
        }
      },
    }),
    [portfolioId]
  );

  return <PortfolioContext.Provider value={value}>{children}</PortfolioContext.Provider>;
}

export function usePortfolio(): PortfolioContextValue {
  const context = useContext(PortfolioContext);
  if (!context) throw new Error("usePortfolio requires PortfolioProvider");
  return context;
}
