FROM node:20-alpine AS build
WORKDIR /ui

# Install dependencies first for better layer caching.
COPY package.json package-lock.json ./
RUN npm ci

# Copy build configuration and source files required by `npm run build`.
COPY tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY vite.config.ts tailwind.config.cjs postcss.config.cjs ./
COPY index.html ./
COPY public ./public
COPY src ./src

RUN npm run build

FROM nginx:alpine
COPY --from=build /ui/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

