import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioProvider } from "@/lib/portfolio-context";
import { CopilotDrawer } from "@/components/copilot/CopilotDrawer";

function renderDrawer(initialPortfolioId: number | null = null) {
  return render(
    <AppProviders>
      <PortfolioProvider initialPortfolioId={initialPortfolioId}>
        <CopilotDrawer open onClose={() => undefined} />
      </PortfolioProvider>
    </AppProviders>
  );
}

describe("CopilotDrawer", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("asks to select a portfolio when none is chosen", () => {
    renderDrawer();
    expect(screen.getByText("Select a portfolio to start chatting.")).toBeInTheDocument();
  });

  it("renders the fetched chat history with token totals", async () => {
    const history = [
      {
        id: 1,
        role: "user",
        content: "How much did I invest?",
        citations: [],
        tokens_in: 0,
        tokens_out: 0,
        created_at: "2026-07-17T10:00:00Z",
      },
      {
        id: 2,
        role: "assistant",
        content: "You invested 5000 in total.",
        citations: [{ id: "run_sql#1", content: "invested_amount=5000" }],
        tokens_in: 42,
        tokens_out: 17,
        created_at: "2026-07-17T10:00:05Z",
      },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input).includes("/api/copilot/info")) {
          return new Response(JSON.stringify({ model: "gemma4:e4b" }), { status: 200 });
        }
        return new Response(JSON.stringify(history), { status: 200 });
      })
    );
    renderDrawer(7);
    await waitFor(() =>
      expect(screen.getByText("You invested 5000 in total.")).toBeInTheDocument()
    );
    expect(screen.getByText("How much did I invest?")).toBeInTheDocument();
    expect(screen.getByText("run_sql#1")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Model: gemma4:e4b")).toBeInTheDocument());

    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fireEvent.click(screen.getByLabelText("clear chat"));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => (call[1] as RequestInit | undefined)?.method === "DELETE"
        )
      ).toBe(true)
    );
    // MUI multiline renders a hidden sizing twin — two textareas share the placeholder
    expect(screen.getAllByPlaceholderText("Ask about this portfolio…").length).toBeGreaterThan(0);
  });

  it("shows a typing indicator while the agent is working", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: unknown, init?: RequestInit) => {
        if (init?.method === "POST") return new Promise<Response>(() => undefined);
        return new Response(JSON.stringify([]), { status: 200 });
      })
    );
    renderDrawer(7);
    const [input] = await screen.findAllByPlaceholderText("Ask about this portfolio…");
    fireEvent.change(input, { target: { value: "Hi" } });
    fireEvent.click(screen.getByLabelText("send message"));
    await waitFor(() => expect(screen.getByLabelText("agent is typing")).toBeInTheDocument());
    expect(screen.getByText("Hi")).toBeInTheDocument();
  });
});
