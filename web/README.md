# Electricity Maps

**This documentation is specifically for the frontend web/mobile app.**

_If you're looking for more info on the parsers, check out [how to setup Python development environment](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Set-up-local-environment#setup-python-development-environment) and [how to fix a broken parser (and test it locally)](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Fixing-a-broken-parser)._

## Local development

Prerequisites:

- Ensure you have `NodeJS` and `yarn` installed locally
- Run `yarn install` in both the web and mockserver directories

After the above steps, simply run the following steps:

1. Start the mockserver: `yarn run mockserver`
2. Run app in another tab: `yarn develop`

### Using production API (internal eMap team only)

As an eMap internal team member, you can also run the app connected to production API instead of the mockserver:

- Run `SNOWPACK_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN='YOUR_TOKEN' yarn develop`
- Add a `?remote=true` query parameter

## Geometries development

See [how to edit world geometries](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Edit-world-geometries).
