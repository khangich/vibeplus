# docker/frontend.Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy manifests first for better caching
COPY package.json package-lock.json* ./

# Install deps (prefer CI when lockfile exists)
RUN if [ -f package-lock.json ]; then npm ci; else npm install --legacy-peer-deps; fi

# Copy the rest of the app
COPY . .

# Provide the backend URL at build time and default it for runtime
ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL

# Build Next.js
RUN npm run build

# Ensure Next listens on 0.0.0.0:8080
ENV PORT=8080
ENV HOST=0.0.0.0
EXPOSE 8080

# Rely on package.json "start" script to honor PORT/HOST
CMD ["npm", "run", "start"]
