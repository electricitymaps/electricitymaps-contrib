FROM node:6.9.2
WORKDIR /home
EXPOSE 8000
ADD package.json /home/package.json
RUN npm install
ADD . /home
CMD node server.js
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

