FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
# App.tsx imports the existing prototype as a raw asset from the repository
# root, so the production build context must include it as well.
COPY livlink-prototype.html /livlink-prototype.html

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
