import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import SatellitePage from "@/app/satellite/page";
import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioProvider } from "@/lib/portfolio-context";

const AVAILABLE_STOCKS = Array.from({ length: 201 }, (_, index) => ({
  ticker: `T${String(index + 1).padStart(3, "0")}`,
  name: `Test stock ${index + 1}`,
  sector: "Information Technology",
  market_cap: 1_000_000,
  pe_trailing: 10,
  cagr_10y: 0.1,
  earnings_yield: 0.1,
  roic: 0.2,
  magic_rank: index + 1,
}));

function stubScreenerApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), "http://localhost");
      if (url.pathname === "/api/market/screener") {
        const limit = url.searchParams.get("limit");
        const rows = limit ? AVAILABLE_STOCKS.slice(0, Number(limit)) : AVAILABLE_STOCKS;
        return new Response(JSON.stringify(rows), { status: 200 });
      }
      return new Response(JSON.stringify([]), { status: 200 });
    })
  );
}

function stubStorage() {
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, value),
      removeItem: (key: string) => void store.delete(key),
      clear: () => store.clear(),
    },
  });
}

describe("SatellitePage", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("makes every available screener row pageable", async () => {
    stubStorage();
    stubScreenerApi();

    render(
      <AppProviders>
        <PortfolioProvider>
          <SatellitePage />
        </PortfolioProvider>
      </AppProviders>
    );

    expect(await screen.findByText(/of 201/)).toBeInTheDocument();
  });
});
