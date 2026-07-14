# Cloud Run Demo A — Vite / TanStack frontend (preview server)
FROM node:22-bookworm-slim AS build

WORKDIR /app

ARG VITE_API_BASE_URL=http://127.0.0.1:8001
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-bookworm-slim

WORKDIR /app
ENV NODE_ENV=production \
    HOST=0.0.0.0

COPY --from=build /app /app

EXPOSE 8080

# Build output is a Cloudflare-style fetch worker (dist/server/server.js), not a
# Node listener. For Demo A use Vite preview with allowedHosts enabled.
CMD ["sh", "-c", "exec npx --yes vite preview --host 0.0.0.0 --port ${PORT:-8080}"]
