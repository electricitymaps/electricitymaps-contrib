FROM node:6.9.2
WORKDIR /home
EXPOSE 8000
RUN curl -o- -L https://yarnpkg.com/install.sh | bash
ADD package.json /home/package.json
ADD yarn.lock /home/yarn.lock
RUN $HOME/.yarn/bin/yarn install
ADD . /home
CMD node server.js
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

