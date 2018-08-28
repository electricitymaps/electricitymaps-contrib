FROM node:10.9.0
WORKDIR /home/web

# Install dependencies
RUN apt-get update && apt-get install -y unzip
ADD web/package.json /home/web/package.json
ADD web/yarn.lock /home/web/yarn.lock
RUN yarn

# Add sources
ADD config /home/config
ADD web /home/web

# Generate map
RUN bash topogen.sh

ARG ELECTRICITYMAP_PUBLIC_TOKEN

# Build
RUN yarn run build-release

EXPOSE 8000
CMD node server.js

HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1
