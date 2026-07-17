import { describe, expect, it } from "vitest";

import { formatMoney, formatNumber, formatPercent } from "@/lib/format";

describe("formatNumber", () => {
  it("caps decimals at 2", () => {
    expect(formatNumber(24.084322)).toBe("24.08");
  });

  it("compacts millions and billions", () => {
    expect(formatNumber(7_000_000)).toBe("7M");
    expect(formatNumber(141_647_790_080)).toBe("141.6B");
  });

  it("handles null and undefined", () => {
    expect(formatNumber(null)).toBe("n/a");
    expect(formatNumber(undefined)).toBe("n/a");
  });

  it("keeps small integers plain", () => {
    expect(formatNumber(200)).toBe("200");
  });
});

describe("formatMoney", () => {
  it("compacts large amounts with currency symbol", () => {
    expect(formatMoney(7_000_000)).toBe("$7M");
    expect(formatMoney(141_647_790_080)).toBe("$141.6B");
  });

  it("shows small amounts with cents", () => {
    expect(formatMoney(1234.5)).toBe("$1,234.50");
  });

  it("respects the currency code", () => {
    expect(formatMoney(5_000_000, "EUR")).toBe("€5M");
  });

  it("handles null", () => {
    expect(formatMoney(null)).toBe("n/a");
  });
});

describe("formatPercent", () => {
  it("renders a fraction as percent with one decimal by default", () => {
    expect(formatPercent(0.104)).toBe("10.4%");
  });

  it("supports zero decimals", () => {
    expect(formatPercent(0.7, 0)).toBe("70%");
  });

  it("handles null", () => {
    expect(formatPercent(null)).toBe("n/a");
  });
});
