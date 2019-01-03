FROM node:10.9.0
WORKDIR /home/web

# Install dependencies
RUN apt-get update && apt-get install -y unzip
ADD web/package.json /home/web/package.json
ADD web/yarn.lock /home/web/yarn.lock
RUN yarn

# Generate map
RUN mkdir -p public/dist/
ADD web/build /home/web/build
ADD web/third_party_maps /home/web/third_party_maps
ADD web/generate-geometries.js web/topogen.sh /home/web/
ADD web/src/world.json /home/web/src/world.json
RUN bash topogen.sh

ARG ELECTRICITYMAP_PUBLIC_TOKEN

# Build
# (note: this will override the world.json that was previously created)
ADD config /home/config
ADD web /home/web
RUN yarn run build-release

EXPOSE 8000
ENV PORT 8000
CMD node server.js

HEALTHCHECK CMD curl --fail http://localhost:${PORT}/ || exit 1
