FROM node:6.9.2
WORKDIR /home
EXPOSE 8000
ADD package.json /home/package.json
RUN npm install
ADD . /home
RUN npm run build-release
CMD node server.js
# Healthcheck removed for now because Docker > 1.10 not supported by circle ci
# HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

