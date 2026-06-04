FROM node:22-alpine AS build

WORKDIR /app
COPY package.json .
RUN npm install

COPY . .
RUN npm run build

# Nginx 静态服务
FROM nginx:alpine
COPY --from=build /app/../backend/static /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
