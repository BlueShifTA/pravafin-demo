# Frontend (Next.js standalone), built with pnpm.
# Build context = repo root.
#   docker build -f devops/frontend.Dockerfile -t coresat-frontend .
# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS build
WORKDIR /app
RUN corepack enable
# Deps first — cached until the lockfile changes.
COPY projects/frontend/package.json projects/frontend/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
COPY projects/frontend/ ./
# public/ is optional (absent today); guarantee it exists so the runtime COPY
# always resolves and picks up assets if they are added later.
RUN mkdir -p public
# Next.js bakes rewrite destinations at build time, so the backend origin must
# be set HERE (not at runtime). Defaults to the compose service name.
ARG BACKEND_ORIGIN=http://backend:8000
ENV BACKEND_ORIGIN=$BACKEND_ORIGIN
# Generated client is committed, so the build needs no running backend.
RUN pnpm build

FROM node:22-bookworm-slim AS runtime
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0
WORKDIR /app
RUN useradd --create-home --uid 10001 app
# Standalone output bundles a minimal node_modules + server.js.
COPY --from=build --chown=app:app /app/.next/standalone ./
COPY --from=build --chown=app:app /app/.next/static ./.next/static
COPY --from=build --chown=app:app /app/public ./public
USER app
EXPOSE 3000
CMD ["node", "server.js"]
