FROM node:16-alpine

ENV ARGS=''
WORKDIR /app

COPY package-lock.json package.json ./
RUN npm install --production
COPY . .

EXPOSE 80 443

CMD npm run start ${ARGS}
