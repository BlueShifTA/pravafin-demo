import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioAssistant } from "@/components/wizard/PortfolioAssistant";

const DRAFT = {
  name: "AI Growth",
  initial_capital: 100000,
  monthly_contribution: 500,
  core_fund_ticker: "IWDA.AS",
  core_weight: 0.6,
  satellites: [
    { ticker: "NVDA", weight: 0.2 },
    { ticker: "UNH", weight: 0.2 },
  ],
};

function sse(...events: Array<{ event: string; data: unknown }>): Response {
  const body = events.map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`).join("");
  return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
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
      vi.fn(async () =>
        sse({ event: "answer", data: { text: "Here is a plan.", action: "propose", draft: DRAFT } })
      )
    );
    renderAssistant();
    fireEvent.change(screen.getByPlaceholderText("Describe the portfolio you want…"), {
      target: { value: "build me a tech portfolio" },
    });
    fireEvent.click(screen.getByLabelText("send message"));

    await waitFor(() => expect(screen.getByText("IWDA.AS")).toBeInTheDocument());
    expect(screen.getByText(/NVDA/)).toBeInTheDocument();
    expect(screen.getByText(/UNH/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /build it/i })).toBeInTheDocument();
  });

  it("calls onCreated when the agent confirms creation", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        sse({ event: "answer", data: { text: "Proposal.", action: "propose", draft: DRAFT } })
      )
      .mockResolvedValueOnce(
        sse({ event: "created", data: { portfolio_id: 42, name: "AI Growth" } })
      );
    vi.stubGlobal("fetch", fetchMock);
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
