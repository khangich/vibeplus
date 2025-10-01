FROM node:20-alpine

RUN addgroup -S sandbox && adduser -S sandbox -G sandbox
WORKDIR /workspace
USER sandbox
EXPOSE 8080
CMD ["sh", "-c", "npm ci && npm run build && npm run start -- --hostname 0.0.0.0 --port 8080"]
