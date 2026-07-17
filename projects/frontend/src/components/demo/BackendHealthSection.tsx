"use client";

import { Typography } from "@mui/material";

import { useHealthHealthGet } from "@/lib/generated/endpoints";
import { Section } from "@/components/layout/Section";

export function BackendHealthSection() {
  const healthQuery = useHealthHealthGet({
    query: {
      retry: 1,
      refetchInterval: 15_000,
    },
  });

  if (healthQuery.isLoading) {
    return (
      <Section
        title="Backend"
        description="Generated React Query hook against FastAPI health endpoint."
      >
        <Typography sx={{ fontFamily: "monospace", fontSize: 14 }}>loading...</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Waiting for `/health` via Next.js rewrite.
        </Typography>
      </Section>
    );
  }

  if (healthQuery.isError) {
    return (
      <Section
        title="Backend"
        description="Generated React Query hook against FastAPI health endpoint."
      >
        <Typography sx={{ fontFamily: "monospace", fontSize: 14 }}>unreachable</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {healthQuery.error instanceof Error
            ? healthQuery.error.message
            : "Run `just run-backend` to check health."}
        </Typography>
      </Section>
    );
  }

  const payload = healthQuery.data?.data ?? {};
  const statusCode = healthQuery.data?.status;
  const statusText = payload.status ?? "ok";

  return (
    <Section
      title="Backend"
      description="Generated React Query hook against FastAPI health endpoint."
    >
      <Typography sx={{ fontFamily: "monospace", fontSize: 14 }}>
        healthy
        {statusCode ? ` (${statusCode})` : ""}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        {`status=${statusText}`}
      </Typography>
    </Section>
  );
}
