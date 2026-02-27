FROM node:20-alpine as build
WORKDIR /ui
COPY package.json tsconfig.json vite.config.ts ./
COPY index.html ./
COPY src ./src
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /ui/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

