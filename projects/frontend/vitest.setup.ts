import "@testing-library/jest-dom/vitest";

// jsdom lacks the layout APIs @mui/x-charts probes on render. Stub them so any
// component that draws a chart can be rendered and asserted in tests.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;

if (!("getBBox" in SVGElement.prototype)) {
  Object.defineProperty(SVGElement.prototype, "getBBox", {
    writable: true,
    value: () => ({ x: 0, y: 0, width: 0, height: 0 }),
  });
}
