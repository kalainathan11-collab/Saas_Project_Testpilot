# syntax=docker/dockerfile:1
# ---- build ----
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# ---- serve ----
# Unprivileged nginx (non-root, listens on 8080). The entrypoint runs envsubst over
# /etc/nginx/templates/*.template, writing the results into /etc/nginx/conf.d/.
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
ARG VITE_API_URL=http://localhost:8000
# API origin used in the CSP connect-src; override at runtime with -e API_ORIGIN=...
ENV API_ORIGIN=${VITE_API_URL}
# Only substitute our variable so nginx's own $variables are left alone.
ENV NGINX_ENVSUBST_FILTER=^API_ORIGIN$
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY security-headers.inc.template /etc/nginx/templates/security-headers.inc.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=5     CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
