# ---- frontend image: static HTML served by Nginx ----
FROM nginx:1.27-alpine

# Replace nginx's default site with ours (static files + reverse proxy rules)
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
