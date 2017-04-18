#!/bin/bash
set -eu -o pipefail

# Build assets
rm -rf www || true
rm -rf locales || true
pushd ..
docker-compose build web
popd
CONTAINER_ID=$(docker create electricitymap_web)
docker cp $CONTAINER_ID:/home/web/public/ .
mv public www
docker cp $CONTAINER_ID:/home/web/locales/ .
docker rm $CONTAINER_ID

# Run node in order to build index.html
node generate-index.js
