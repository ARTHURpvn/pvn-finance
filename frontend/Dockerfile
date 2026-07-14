# ---- build do SPA ----
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# URL da API embutida no bundle em build time. Same-origin: o Caddy faz o proxy
# de /api → api:8000, então não há CORS nem URL de backend hardcoded.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---- runtime: Caddy serve o SPA e faz proxy da API ----
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile
