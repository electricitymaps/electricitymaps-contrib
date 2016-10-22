FROM node:4.5.0
WORKDIR /home
EXPOSE 8000
RUN npm install -g yarn
ADD package.json /home/package.json
RUN yarn
ADD . /home
CMD node server.js
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

