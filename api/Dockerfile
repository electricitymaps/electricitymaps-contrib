FROM node:4.5.0
WORKDIR /home
EXPOSE 8000
ADD package.json /home/package.json
RUN npm install
ADD . /home
CMD node index.js
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

