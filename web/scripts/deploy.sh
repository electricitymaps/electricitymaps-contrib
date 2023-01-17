#!/bin/bash

echo "Starting deployment..."

# Ensure required environment variables are set
if [ -z "$SUBDOMAIN" ]; then
  echo "SUBDOMAIN is not set - must be beta or app"
  exit 1
fi
if [ -z "$VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN" ]; then
  echo "VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN is not set"
  exit 1
fi
if [ -z "$SENTRY_AUTH_TOKEN" ]; then
  echo "SENTRY_AUTH_TOKEN is not set"
  exit 1
fi

BUCKET_NAME="gs://$SUBDOMAIN.electricitymaps.com"

# Create bucket and ensure everything is public - only required first time
# gsutil mb -p tmrow-152415 -c regional -l europe-west1 $BUCKET_NAME || true
# gsutil iam ch allUsers:objectViewer $BUCKET_NAME

# Upload files and set proper index page
gsutil -m cp -a public-read -r dist/* $BUCKET_NAME
gsutil web set -m index.html -e index.html $BUCKET_NAME

# Unsure if this is required, but we have used it before...
# Save the following to cors-config.json and enable command below
# [{"maxAgeSeconds": 3600,"method": ["GET", "HEAD"],"origin": ["*"],"responseHeader": ["Content-Type"]}]
# gsutil cors set cors-config.json $BUCKET_NAME

# Set no-cache for certain files if required
gsutil setmeta -h "Cache-Control:no-cache,max-age=0" $BUCKET_NAME/client-version.json
gsutil setmeta -h "Cache-Control:no-cache,max-age=0" $BUCKET_NAME/index.html
gsutil -m setmeta -h "Cache-Control:no-cache,max-age=0" "$BUCKET_NAME/**/index.html"
#gsutil setmeta -h "Cache-Control:no-cache,max-age=0" $BUCKET_NAME/*.json

# Create new git tag and Github release
VERSION=$(npm pkg get version | tr -d '"')
git tag -a $VERSION -m "$VERSION"
git push origin $VERSION
gh release create $VERSION --generate-notes --repo electricitymaps/electricitymaps-contrib-rewrite

echo "Done!"