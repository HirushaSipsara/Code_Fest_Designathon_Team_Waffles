FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
# The project currently has no package-lock.json. Add one before a production
# release, then replace this with `npm ci` for fully reproducible builds.
RUN npm install --no-audit --no-fund

COPY . ./

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
