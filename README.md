# electricityMap

[![Slack Status](https://slack.tmrow.com/badge.svg)](https://slack.tmrow.com) [![CircleCI](https://circleci.com/gh/tmrowco/electricitymap-contrib.svg?style=shield)](https://circleci.com/gh/tmrowco/electricitymap-contrib) [![Twitter Follow](https://img.shields.io/twitter/follow/electricitymap.svg?style=social&label=Follow)](https://twitter.com/electricitymap)

A real-time visualisation of the Greenhouse Gas (in terms of CO<sub>2</sub> equivalent) footprint of electricity consumption built with [d3.js](https://d3js.org/) and [mapbox GL](https://github.com/mapbox/mapbox-gl-js/), maintained by [Tomorrow](https://www.tmrow.com). Try it out at [http://www.electricitymap.org](http://www.electricitymap.org), or download the app on [Google Play](https://play.google.com/store/apps/details?id=com.tmrow.electricitymap&utm_source=github) or [App store](https://itunes.apple.com/us/app/electricity-map/id1224594248&utm_source=github).

![image](https://www.electricitymap.org/images/electricitymap_social_image.jpg)


## Contribute
Thank you for your interest. Check out the [Wiki](https://github.com/tmrowco/electricitymap-contrib/wiki) for how to get started. Also, have a look at our current [issues](https://github.com/tmrowco/electricitymap-contrib/issues) and [discussions](https://github.com/tmrowco/electricitymap-contrib/discussions)

Here are some of the ways you can contribute:
 * [Building a new parser](https://github.com/tmrowco/electricitymap-contrib/wiki/Building-a-new-parser)
 * [Fixing a broken parser](https://github.com/tmrowco/electricitymap-contrib/wiki/Fixing-a-broken-parser)
 * [Changes to the frontend](https://github.com/tmrowco/electricitymap-contrib/wiki/Changes-to-the-frontend)
 * [Find data sources](https://github.com/tmrowco/electricitymap-contrib/wiki/Find-data-sources)
 * [Verify data sources](https://github.com/tmrowco/electricitymap-contrib/wiki/Verify-data-sources)
 * [Translating electricitymap.org](https://github.com/tmrowco/electricitymap-contrib/wiki/Translating-electricitymap.org)
 * [Updating region capacities](https://github.com/tmrowco/electricitymap-contrib/wiki/Update-region-capacities)


Join us on [Slack](https://slack.tmrow.com) if you wish to discuss development or need help to get started.

We would love your feedback on how to improve the contribution experience, please feel free to fill out this [form](https://forms.gle/VRWvEFwhtnhpzPVX8)

## Frequently asked questions

**Where does the data come from?**
The data comes from many different sources. You can check them out [here](https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md)

**How do you define real-time data?**
Real-time data is defined as a data source with an hourly (or better) frequency, delayed by less than 2hrs. It should provide a breakdown by generation type. Often fossil fuel generation (coal/gas/oil) is combined under a single heading like 'thermal' or 'conventional', this is not a problem.

**Why do you calculate the carbon intensity of *consumption*?**
In short, citizens should not be responsible for the emissions associated with all the products they export, but only for what they consume.
Consumption-based accounting (CBA) is a very important aspect of climate policy and allows assigning responsibility to consumers instead of producers.
Furthermore, this method is robust to governments relocating dirty production to neighboring countries in order to green their image while still importing from it.
We published our methodology [here](https://arxiv.org/abs/1812.06679).

**Why don't you show emissions per capita?**
A country that has few inhabitants but a lot of factories will appear high on CO<sub>2</sub>/capita.
This means you can "trick" the numbers by moving your factory abroad and import the produced *good* instead of the electricity itself.
That country now has a low CO<sub>2</sub>/capita number because we only count CO<sub>2</sub> for electricity (not for imported/exported goods).
The CO<sub>2</sub>/capita metric, by involving the size of the population, and by not integrating all CO<sub>2</sub> emission sources, is thus an incomplete metric.
CO<sub>2</sub> intensity on the other hand only describes where is the best place to put that factory (and when it is best to use electricity), enabling proper decisions.

**CO<sub>2</sub> emission factors look high — what do they cover exactly?**
The carbon intensity of each type of power plant takes into account emissions arising from the whole life cycle of the plant (construction, fuel production, operational emissions and decommissioning).

**Is delayed data useful?**
While the map relies on having real-time data to work it's still useful to collect data from days/months past. This older data can be used to show past emissions and build up a better dataset. So if there's an hourly data source that lags several days behind you can still build a parser for it.

**Can scheduled/assumed generation data be used?**
The electricityMap doesn't use scheduled generation data or make assumptions about unknown fuel mixes. This is to avoid introducing extra uncertainty into emissions calculations.

**Can areas other than countries be shown?**
Yes, providing there is a valid GeoJSON geometry (or another format that can be converted) for the area. As an example, we already split several countries into states and grid regions.

**How can I get access to historical data or the live API?**
All this and more can be found **[here](https://api.electricitymap.org/)**.

