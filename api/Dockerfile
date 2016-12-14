FROM node:6.9.2
WORKDIR /home
EXPOSE 8000
RUN npm install -g yarn
ADD package.json /home/package.json
ADD yarn.lock /home/yarn.lock
# Workaround for yarn to be able to chown
RUN adduser foo
RUN chown -R foo /home/foo
RUN chown -R foo /usr/local
USER foo

RUN yarn install
ADD . /home
CMD node server.js
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

