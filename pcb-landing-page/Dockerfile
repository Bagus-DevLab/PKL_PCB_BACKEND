# === TAHAP 1: BUILD ===
FROM node:20-alpine as build-stage

# Set working directory di dalam container
WORKDIR /app

# Copy package.json dan package-lock.json (kalau ada)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy seluruh source code
COPY . .

# Build project Vite-nya
RUN npm run build


# === TAHAP 2: SERVE DENGAN NGINX ===
FROM nginx:alpine as production-stage

# Hapus default konfigurasi Nginx bawaan
RUN rm -rf /usr/share/nginx/html/*

# Copy hasil build dari Tahap 1 (folder dist) ke folder Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration untuk SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 di dalam container
EXPOSE 80

# Jalankan Nginx
CMD ["nginx", "-g", "daemon off;"]