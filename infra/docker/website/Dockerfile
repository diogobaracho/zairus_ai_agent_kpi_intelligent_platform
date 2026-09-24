# syntax=docker/dockerfile:1
FROM node:24-alpine AS builder
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/website/package.json apps/website/package.json
RUN pnpm install --frozen-lockfile --filter website...
COPY brand.config.json ./
COPY apps/website apps/website
ARG VITE_CHAT_URL=http://localhost:3000
ARG VITE_API_DOCS_URL=http://localhost:8080/docs
ENV VITE_CHAT_URL=$VITE_CHAT_URL VITE_API_DOCS_URL=$VITE_API_DOCS_URL
RUN pnpm --filter website build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
COPY infra/docker/website/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/apps/website/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
