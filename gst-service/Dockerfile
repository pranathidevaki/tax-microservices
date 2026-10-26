# ---- gst-service image ----
FROM node:22-alpine

WORKDIR /app

# Install only production dependencies, using the exact versions in package-lock.json
COPY package*.json ./
RUN npm ci --omit=dev

COPY . .

# The official node image ships with a non-root user called "node"
USER node

EXPOSE 3000
CMD ["node", "server.js"]
