import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BackendHealthSection } from "@/components/demo/BackendHealthSection";
import { useHealthHealthGet } from "@/lib/generated/endpoints";

vi.mock("@/lib/generated/endpoints", () => ({
  useHealthHealthGet: vi.fn(),
}));

const mockedUseHealthHealthGet = vi.mocked(useHealthHealthGet);

type HealthQueryResult = ReturnType<typeof useHealthHealthGet>;

function renderWithClient(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("BackendHealthSection", () => {
  it("shows a loading indicator while the health query is pending", () => {
    mockedUseHealthHealthGet.mockReturnValue({
      isLoading: true,
      isError: false,
    } as HealthQueryResult);

    renderWithClient(<BackendHealthSection />);

    expect(screen.getByText("loading...")).toBeInTheDocument();
  });

  it("shows the error message when the health query fails", () => {
    mockedUseHealthHealthGet.mockReturnValue({
      isLoading: false,
      isError: true,
      error: new Error("backend down"),
    } as HealthQueryResult);

    renderWithClient(<BackendHealthSection />);

    expect(screen.getByText("unreachable")).toBeInTheDocument();
    expect(screen.getByText("backend down")).toBeInTheDocument();
  });

  it("shows the healthy status text when the backend responds", () => {
    mockedUseHealthHealthGet.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { data: { status: "ok" }, status: 200 },
    } as HealthQueryResult);

    renderWithClient(<BackendHealthSection />);

    expect(screen.getByText(/^healthy/)).toBeInTheDocument();
    expect(screen.getByText("status=ok")).toBeInTheDocument();
  });
});
