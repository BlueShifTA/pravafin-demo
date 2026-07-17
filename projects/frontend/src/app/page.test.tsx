import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioProvider } from "@/lib/portfolio-context";
import DashboardPage from "@/app/page";

describe("DashboardPage", () => {
  it("shows the empty state when no portfolio is selected", () => {
    render(
      <AppProviders>
        <PortfolioProvider>
          <DashboardPage />
        </PortfolioProvider>
      </AppProviders>
    );
    expect(screen.getByText("No portfolio selected.")).toBeInTheDocument();
  });
});
