import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: "./openapi.json",
    output: {
      target: "./src/lib/generated/endpoints.ts",
      client: "react-query",
      httpClient: "fetch",
      mode: "split",
      schemas: "./src/lib/generated/models",
      override: {
        query: {
          useQuery: true,
          useMutation: true,
          useInfinite: true,
          signal: true,
        },
      },
      prettier: true,
    },
  },
});
