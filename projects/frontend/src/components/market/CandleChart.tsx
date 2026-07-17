"use client";

import { Box } from "@mui/material";
import { CandlestickSeries, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { CandleBar } from "@/lib/generated/models";

// useEffect is justified here: lightweight-charts is an imperative canvas
// library that must mount into a real DOM node.
export function CandleChart({ bars }: { bars: CandleBar[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || bars.length === 0) return;
    const chart = createChart(containerRef.current, {
      height: 320,
      autoSize: true,
      layout: { attributionLogo: false },
    });
    const series = chart.addSeries(CandlestickSeries);
    series.setData(
      bars
        .filter((bar) => bar.open != null && bar.high != null && bar.low != null)
        .map((bar) => ({
          time: bar.date,
          open: bar.open as number,
          high: bar.high as number,
          low: bar.low as number,
          close: bar.close,
        }))
    );
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [bars]);

  return <Box ref={containerRef} sx={{ width: "100%", height: 320 }} />;
}
