FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json /app/
RUN npm install

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=development

COPY --from=deps /app/node_modules /app/node_modules
COPY . /app

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
