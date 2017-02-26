FROM node:6.9.4
WORKDIR /home/web

ADD web/package.json /home/web/package.json
RUN npm install

ADD web /home/web
ADD shared /home/shared

RUN npm run build-release

EXPOSE 8000
CMD node server.js

HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1
