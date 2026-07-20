import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import CorePage from "@/app/core/page";
import { AppProviders } from "@/components/layout/AppProviders";

const FUNDS = [
  {
    ticker: "CSPX",
    name: "iShares Core S&P 500",
    provider: null,
    category: "US Equity",
    currency: "USD",
    fund_size: 1_000_000_000,
    ter: 0.07,
    dist_yield: null,
    cagr_5y: 0.12,
    cagr_10y: 0.13,
    holdings_count: 500,
  },
  {
    ticker: "VUAA",
    name: "Vanguard S&P 500",
    provider: null,
    category: "US Equity",
    currency: "USD",
    fund_size: 500_000_000,
    ter: 0.07,
    dist_yield: null,
    cagr_5y: 0.12,
    cagr_10y: 0.12,
    holdings_count: 500,
  },
  {
    ticker: "SWDA",
    name: "iShares MSCI World",
    provider: null,
    category: "Global Equity",
    currency: "USD",
    fund_size: 800_000_000,
    ter: 0.2,
    dist_yield: null,
    cagr_5y: 0.1,
    cagr_10y: 0.11,
    holdings_count: 1500,
  },
];

function json(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Core (ETF) page fund comparison", () => {
  function mount() {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const target = String(url instanceof Request ? url.url : url);
        if (target.includes("/market/funds")) return json(FUNDS);
        return json([]);
      })
    );
    render(
      <AppProviders>
        <CorePage />
      </AppProviders>
    );
  }

  it("selects Fund A and Fund B from the table, not a dropdown list", async () => {
    mount();
    await waitFor(() => expect(screen.getByText("CSPX")).toBeInTheDocument());

    // the dropdown pickers are gone — selection comes from the table
    expect(screen.queryByLabelText("Fund A")).toBeNull();
    expect(screen.queryByLabelText("Fund B")).toBeNull();

    // a hint until two funds are picked
    expect(screen.getByText(/select two funds/i)).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // CSPX
    fireEvent.click(checkboxes[2]); // SWDA

    // the comparison populates: its stats table header appears, hint is gone
    await waitFor(() => expect(screen.getByText(/net after 20y/i)).toBeInTheDocument());
    expect(screen.queryByText(/select two funds/i)).toBeNull();
  });

  it("caps the table selection at two funds", async () => {
    mount();
    await waitFor(() => expect(screen.getByText("CSPX")).toBeInTheDocument());

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);
    // third checkbox is disabled once two are chosen
    expect(checkboxes[2]).toBeDisabled();
  });
});
