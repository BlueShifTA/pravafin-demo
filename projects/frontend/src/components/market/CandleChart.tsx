"use client";

import { Box } from "@mui/material";
import { CandlestickSeries, LineSeries, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { CandleBar, IndicatorPoint } from "@/lib/generated/models";

const OVERLAYS = [
  { key: "sma_20", label: "SMA 20", color: "#4caf50" },
  { key: "sma_50", label: "SMA 50", color: "#ff9800" },
  { key: "sma_200", label: "SMA 200", color: "#f44336" },
] as const;

type CandleChartProps = {
  bars: CandleBar[];
  indicators?: IndicatorPoint[];
};

// useEffect is justified here: lightweight-charts is an imperative canvas
// library that must mount into a real DOM node.
export function CandleChart({ bars, indicators }: CandleChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || bars.length === 0) return;
    const chart = createChart(containerRef.current, {
      height: 320,
      autoSize: true,
      layout: { attributionLogo: false },
    });
    const series = chart.addSeries(CandlestickSeries);
    const candleData = bars
      .filter((bar) => bar.open != null && bar.high != null && bar.low != null)
      .map((bar) => ({
        time: bar.date,
        open: bar.open as number,
        high: bar.high as number,
        low: bar.low as number,
        close: bar.close,
      }));
    series.setData(candleData);
    for (const overlay of OVERLAYS) {
      const line = chart.addSeries(LineSeries, {
        color: overlay.color,
        lineWidth: 1,
        title: overlay.label,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      line.setData(
        (indicators ?? [])
          .filter((point) => point[overlay.key] != null)
          .map((point) => ({ time: point.date, value: point[overlay.key] as number }))
      );
    }
    // clamp the x-axis to the candles' own range so a longer SMA warm-up window
    // does not stretch the time scale past the visible candles.
    if (candleData.length > 0) {
      chart.timeScale().setVisibleRange({
        from: candleData[0].time,
        to: candleData[candleData.length - 1].time,
      });
    } else {
      chart.timeScale().fitContent();
    }
    return () => chart.remove();
  }, [bars, indicators]);

  return <Box ref={containerRef} sx={{ width: "100%", height: 320 }} />;
}
