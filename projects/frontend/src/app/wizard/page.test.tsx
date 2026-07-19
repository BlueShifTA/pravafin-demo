import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "@/components/layout/AppProviders";
import { AppNav } from "@/components/layout/AppNav";
import { PortfolioProvider } from "@/lib/portfolio-context";
import WizardPage from "@/app/wizard/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/wizard",
}));

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

const FUND = { ticker: "IWDA", name: "iShares Core MSCI World", ter: 0.2, cagr_10y: 0.08 };
const SCREENER_ROW = { ticker: "NVDA", magic_rank: 1 };

function stubApi() {
  let created = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/portfolios") && init?.method === "POST") {
        created = true;
        return new Response(JSON.stringify({ id: 9 }), { status: 201 });
      }
      if (url.endsWith("/api/portfolios")) {
        const list = created
          ? [{ id: 9, name: "My portfolio", created_at: "2026-07-17T10:00:00Z" }]
          : [];
        return new Response(JSON.stringify(list), { status: 200 });
      }
      if (url.includes("/api/market/funds")) {
        return new Response(JSON.stringify([FUND]), { status: 200 });
      }
      if (url.includes("/api/market/screener")) {
        return new Response(JSON.stringify([SCREENER_ROW]), { status: 200 });
      }
      return new Response(JSON.stringify([]), { status: 200 });
    })
  );
}

describe("WizardPage", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the created portfolio in the header selector", async () => {
    stubStorage();
    stubApi();
    render(
      <AppProviders>
        <PortfolioProvider>
          <AppNav>
            <WizardPage />
          </AppNav>
        </PortfolioProvider>
      </AppProviders>
    );

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(await screen.findByText("IWDA"));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    // satellite step is now the screener DataGrid — select the NVDA row via its checkbox
    fireEvent.click(await screen.findByRole("checkbox", { name: /select all rows/i }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Create portfolio" }));

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toHaveTextContent("My portfolio");
    });
  });
});
