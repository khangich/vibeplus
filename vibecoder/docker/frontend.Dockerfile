FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package.json
COPY frontend/package-lock.json frontend/package-lock.json 2>/dev/null || true
COPY frontend .

RUN npm install --legacy-peer-deps
RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "start"]
