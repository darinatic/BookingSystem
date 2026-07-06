# Build the Vue app. VITE_API_BASE_URL is a build-time value baked into the bundle.
FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve the static build with nginx, listening on $PORT (Render sets this).
FROM nginx:alpine
ENV PORT=80
ENV NGINX_ENVSUBST_FILTER=PORT
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
