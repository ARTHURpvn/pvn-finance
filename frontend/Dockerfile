# ---- build do SPA ----
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# URL da API embutida no bundle em build time. Same-origin: o nginx faz o proxy
# de /api → api:8000, então não há CORS nem URL de backend hardcoded.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---- runtime: nginx serve o SPA e faz proxy da API ----
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
