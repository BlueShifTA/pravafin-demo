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

export function formatPercent(fraction: number | null | undefined, decimals: number = 1): string {
  if (fraction == null) return "n/a";
  return `${(fraction * 100).toFixed(decimals)}%`;
}
