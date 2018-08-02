FROM node:8.5.0
WORKDIR /home/web

RUN apt-get update && apt-get install -y unzip
ADD web/package.json /home/web/package.json
ADD web/yarn.lock /home/web/yarn.lock
RUN yarn

ADD web /home/web
ADD config /home/config

ARG ELECTRICITYMAP_PUBLIC_TOKEN

RUN bash topogen.sh
RUN yarn run build-release

EXPOSE 8000
CMD node server.js

HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1
