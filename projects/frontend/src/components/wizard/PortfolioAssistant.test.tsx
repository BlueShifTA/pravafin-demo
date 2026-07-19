import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioAssistant } from "@/components/wizard/PortfolioAssistant";

const DRAFT = {
  name: "AI Growth",
  initial_capital: 100000,
  monthly_contribution: 500,
  cores: [{ ticker: "IWDA.AS", weight: 0.6 }],
  satellites: [
    { ticker: "NVDA", weight: 0.2 },
    { ticker: "UNH", weight: 0.2 },
  ],
};

const FUNDS = [{ ticker: "IWDA.AS", name: "iShares Core MSCI World", ter: 0.2, cagr_10y: 0.1 }];
const SCREENER = [
  { ticker: "NVDA", name: "NVIDIA", cagr_10y: 0.3 },
  { ticker: "UNH", name: "UnitedHealth", cagr_10y: 0.12 },
];

function sse(...events: Array<{ event: string; data: unknown }>): Response {
  const body = events.map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`).join("");
  return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

function json(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

// The DraftCard fetches market data (funds + screener) for its weighted stat
// tiles, so the mock must route by URL — not by call order — or those requests
// would consume the queued draft-chat responses.
function mockFetch(draftResponses: Response[]) {
  const queued = [...draftResponses];
  return vi.fn(async (url: string | URL | Request) => {
    const target = String(url instanceof Request ? url.url : url);
    if (target.includes("/market/funds")) return json(FUNDS);
    if (target.includes("/market/screener")) return json(SCREENER);
    return queued.shift() ?? sse();
  });
}

function renderAssistant(onCreated = vi.fn()) {
  render(
    <AppProviders>
      <PortfolioAssistant onCreated={onCreated} />
    </AppProviders>
  );
  return onCreated;
}

describe("PortfolioAssistant", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the proposed draft as a summary card", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch([
        sse({
          event: "answer",
          data: { text: "Here is a plan.", action: "propose", draft: DRAFT },
        }),
      ])
    );
    renderAssistant();
    fireEvent.change(screen.getByPlaceholderText("Describe the portfolio you want…"), {
      target: { value: "build me a tech portfolio" },
    });
    fireEvent.click(screen.getByLabelText("send message"));

    await waitFor(() => expect(screen.getByText("IWDA.AS")).toBeInTheDocument());
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("UNH")).toBeInTheDocument();
    expect(screen.getByText("Core weighted TER")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /build it/i })).toBeInTheDocument();
  });

  it("calls onCreated when the agent confirms creation", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch([
        sse({ event: "answer", data: { text: "Proposal.", action: "propose", draft: DRAFT } }),
        sse({ event: "created", data: { portfolio_id: 42, name: "AI Growth" } }),
      ])
    );
    const onCreated = renderAssistant();

    fireEvent.change(screen.getByPlaceholderText("Describe the portfolio you want…"), {
      target: { value: "build me a tech portfolio" },
    });
    fireEvent.click(screen.getByLabelText("send message"));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /build it/i })).toBeInTheDocument()
    );

    fireEvent.click(screen.getByRole("button", { name: /build it/i }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(42));
  });
});
