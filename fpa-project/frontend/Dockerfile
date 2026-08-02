# Stage 1: Build the React application
FROM node:20-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the static assets from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the Nginx configuration template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Read PORT from environment — Cloud Run sets this dynamically
ENV PORT=8080
ENV BACKEND_API_URL=""
ENV INGESTION_API_URL=""
# Filter substitution to prevent envsubst from wiping Nginx variables ($uri, $remote_addr, etc.)
ENV NGINX_ENVSUBST_FILTER="PORT BACKEND_API_URL INGESTION_API_URL"

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
