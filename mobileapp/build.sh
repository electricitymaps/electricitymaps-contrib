#!/bin/bash
set -eu -o pipefail

# Extract
CONTAINER_ID=$(docker create eu.gcr.io/tmrow-152415/electricitymap_web:latest)

rm -rf www/electricitymap || true
docker cp $CONTAINER_ID:/home/web/public/ www/electricitymap

rm -rf locales || true
docker cp $CONTAINER_ID:/home/web/locales/ .
docker cp $CONTAINER_ID:/home/web/src .

docker rm $CONTAINER_ID

# Run node in order to build index.html
echo 'Generating index pages..'
yarn add ejs
node generate-index.js

# Generate icons
app-icon generate -i icon_ios.png --platforms=ios
app-icon generate -i icon_android.png --platforms=android
