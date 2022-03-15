*This file should host other explanations. Yours are welcome.*

## Local development

See [local development setup](https://github.com/tmrowco/electricitymap-contrib/wiki/Set-up-local-environment#running-the-frontend-map) in the wiki.


### `geometries-config.js`

The variables `zoneDefinitions` should be updated manually to reflect intended changes in mapping between electricityMap zones and NACIS geometries. It relates each zone from the electricityMap to how it is described by data from NACIS (or third party). A zone can correspond to a country, a group of countries, a state, a group of states...


## `generate-zone-bounding-boxes.js`

You can create bounding boxes for new or existing zones in `config/zones.json`:
1) Update the zone you want to update in `config/zones.json` with `"bounding_box": null`
2) Run: `node geo/generate-zone-bounding-boxes.js`

## Useful tips

- [geojson.io](https://geojson.io) is a great tool for visualizing and editing coordinates
- We currently can't generate coordinates for small islands --> any PRs for fixing this without compromising too much on bundle size is very welcome!


## Translating strings missing in your locale

We wrote a little tool for this task:

```bash
node translation-helper.js
```

You will be asked to select a language to translate.

Running the tool looks like this:

```
Languages you can translate: ar, da, de, es, fr, hr, it, ja, nl, pl, pt-br, ru, sv, zh-cn, zh-hk, zh-tw
Which language do you want to translate: de

country-panel.electricity [Electricity]: Elektrizität
zoneShortName.IQ-KUR.countryName [Iraq]: Irak
...
```
