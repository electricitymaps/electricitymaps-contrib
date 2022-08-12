FROM node:16.15
WORKDIR /home/src/electricitymap/contrib/web

# Install dependencies
RUN apt-get update && apt-get install -y jq unzip
ADD web/package.json ./package.json
ADD web/yarn.lock ./yarn.lock
ADD web/generate-zones-config.js ./generate-zones-config.js
ADD config/ ../config/
RUN yarn install --frozen-lockfile


ADD web/src/world.json ./src/world.json
ARG ELECTRICITYMAP_PUBLIC_TOKEN

# Build
# (note: this will override the world.json that was previously created)
ADD config /home/src/electricitymap/contrib/config
ADD web ./
RUN yarn build-release
RUN yarn verify-zones-config

EXPOSE 8000
ENV PORT 8000
CMD node server.js

HEALTHCHECK CMD curl --fail http://localhost:${PORT}/ || exit 1
