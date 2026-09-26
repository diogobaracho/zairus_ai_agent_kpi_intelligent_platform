# syntax=docker/dockerfile:1
FROM node:24-alpine AS builder
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/chat-web/package.json apps/chat-web/package.json
RUN pnpm install --frozen-lockfile --filter chat-web...
COPY brand.config.json ./
COPY apps/chat-web apps/chat-web
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN pnpm --filter chat-web build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
COPY infra/docker/chat-web/nginx.conf /etc/nginx/templates/default.conf.template
ENV API_UPSTREAM=http://api:8080
COPY --from=builder /app/apps/chat-web/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
