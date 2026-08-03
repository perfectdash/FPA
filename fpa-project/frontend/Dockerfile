FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
ENV PORT=8080
ENV BACKEND_API_URL=""
ENV INGESTION_API_URL=""
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
