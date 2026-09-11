FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_API_URL=/api
RUN npm run build
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# The official entrypoint discovers resolvers from /etc/resolv.conf. Restrict
# substitution to that value so native Nginx variables remain intact.
ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
ENV NGINX_ENVSUBST_FILTER=NGINX_LOCAL_RESOLVERS
COPY nginx.conf /etc/nginx/templates/default.conf.template
