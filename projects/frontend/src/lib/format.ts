const COMPACT_THRESHOLD = 1_000_000;

const compactNumber = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const plainNumber = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

const currencyFormatters = new Map<
  string,
  { compact: Intl.NumberFormat; plain: Intl.NumberFormat }
>();

function currencyFormatter(currency: string) {
  let formatters = currencyFormatters.get(currency);
  if (!formatters) {
    formatters = {
      compact: new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        notation: "compact",
        maximumFractionDigits: 1,
      }),
      plain: new Intl.NumberFormat("en-US", { style: "currency", currency }),
    };
    currencyFormatters.set(currency, formatters);
  }
  return formatters;
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "n/a";
  return Math.abs(value) >= COMPACT_THRESHOLD
    ? compactNumber.format(value)
    : plainNumber.format(value);
}

export function formatMoney(value: number | null | undefined, currency: string = "USD"): string {
  if (value == null) return "n/a";
  const formatters = currencyFormatter(currency);
  return Math.abs(value) >= COMPACT_THRESHOLD
    ? formatters.compact.format(value)
    : formatters.plain.format(value);
}

// Always-compact currency for chart axis ticks: 500K, 2M, 142B (never truncated).
export function formatMoneyCompact(
  value: number | null | undefined,
  currency: string = "USD"
): string {
  if (value == null) return "n/a";
  return currencyFormatter(currency).compact.format(value);
}

export function formatPercent(fraction: number | null | undefined, decimals: number = 1): string {
  if (fraction == null) return "n/a";
  return `${(fraction * 100).toFixed(decimals)}%`;
}

const AXIS_UNITS: [number, string][] = [
  [1_000_000_000, "B"],
  [1_000_000, "M"],
  [1_000, "K"],
];

// Chart y-axis config for money: put the K/M/B unit in the axis title and keep
// the ticks as small plain numbers (title "value ($M)", ticks 0.2, 0.4, …),
// instead of repeating "$0.2M" on every tick. Pick the unit from the largest value.
export function moneyAxis(maxValue: number): {
  label: string;
  valueFormatter: (value: number | null) => string;
} {
  const [unit, suffix] = AXIS_UNITS.find(([threshold]) => maxValue >= threshold) ?? [1, ""];
  return {
    label: `value ($${suffix})`,
    valueFormatter: (value: number | null) => (value == null ? "" : (value / unit).toFixed(1)),
  };
}
