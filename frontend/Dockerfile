FROM node:18-alpine

WORKDIR /usr/src/app
COPY package.json tsconfig.json yarn.lock* package-lock.json* ./
RUN npm install
COPY public/ public/
COPY src/ src/
EXPOSE 3000
CMD ["npm", "start"]
