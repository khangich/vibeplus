FROM node:20-alpine

WORKDIR /app

# Copy package manifests first to leverage Docker layer caching; the glob
# allows the build to succeed even when no lockfile is present.
COPY frontend/package*.json ./
COPY frontend .

RUN npm install --legacy-peer-deps
RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "start"]
