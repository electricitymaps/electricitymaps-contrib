FROM node:8.5.0
WORKDIR /home/web

RUN apt-get update && apt-get install -y unzip
ADD web/package.json /home/web/package.json
ADD web/package-lock.json /home/web/package-lock.json
RUN npm install

ADD web /home/web
ADD config /home/config

ARG ELECTRICITYMAP_PUBLIC_TOKEN
RUN npm run build-release

EXPOSE 8000
CMD node server.js

HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1
