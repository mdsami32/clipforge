# Development Dockerfile for Next.js with hot reload
FROM node:20-slim

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
