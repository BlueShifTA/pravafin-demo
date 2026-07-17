# Frontend

Next.js frontend for the project template application.

## Features

- Next.js 15 with React 18
- TypeScript support
- MUI theme + provider layer
- TanStack React Query for server state
- API proxy configuration to backend
- TailwindCSS for styling
- Type-safe API client generation with orval

## Development

```bash
# Install dependencies
pnpm install

# Run development server
pnpm run dev
```

> **Note:** On first setup, `pnpm install` generates `pnpm-lock.yaml`. Commit this file — CI requires it (`--frozen-lockfile`).

Visit http://localhost:3000

The app uses `src/components/layout/AppProviders.tsx` to configure:

- `QueryClientProvider` (React Query)
- MUI `ThemeProvider` + `CssBaseline`

## API Integration

The frontend is configured to proxy API requests to the backend:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Proxied API calls: `http://localhost:3000/api/*` -> `http://localhost:8000/api/*`
- Health rewrites:
  - `http://localhost:3000/health` -> `http://localhost:8000/health`
  - `http://localhost:3000/ready` -> `http://localhost:8000/ready`

## OpenAPI Code Generation

OpenAPI client code can be generated from the backend API:

```bash
# Generate TypeScript client from OpenAPI spec
pnpm run api
```

This will:

1. Download the OpenAPI spec from the running backend
2. Generate TypeScript types and React Query hooks using Orval (`react-query` mode, `fetch` transport)

## Generated API (Orval + React Query)

Generated files are written to:

- `src/lib/generated/endpoints.ts` (operations + React Query hooks)
- `src/lib/generated/models/*` (schema/types)

The template homepage includes a small example that uses the generated health hook:

- `useHealthHealthGet` from `src/lib/generated/endpoints.ts`

Example usage:

```tsx
import { useHealthHealthGet } from "@/lib/generated/endpoints";

function HealthWidget() {
  const health = useHealthHealthGet();

  if (health.isLoading) return <p>loading...</p>;
  if (health.isError) return <p>unreachable</p>;

  return <pre>{JSON.stringify(health.data?.data, null, 2)}</pre>;
}
```
