<p align="center">
  <a href="https://app.electricitymaps.com">
    <picture>
      <source
        srcset="https://raw.githubusercontent.com/electricitymaps/electricitymaps-contrib/master/.github/images/electricity-maps-logo-dark.svg"
        media="(prefers-color-scheme: dark)"/>
      <img
        alt="Electricity Maps"
        src="https://raw.githubusercontent.com/electricitymaps/electricitymaps-contrib/master/.github/images/electricity-maps-logo.svg"
        width="100"/>
    </picture>
  </a>
</p>
<h1 align="center">
  Electricity Maps
</h1>

<p align="center">
A real time and historical visualisation of the electricity grids around the world.<br>
  <strong><a href="https://app.electricitymaps.com">app.electricitymaps.com »</a></strong>
</p>

<p align="center">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/electricitymaps/electricitymaps-contrib">
  <a href="https://github.com/electricitymaps/electricitymaps-contrib/CONTRIBUTING.md">
    <a href="https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE.md">
    <img src="https://img.shields.io/github/license/electricitymaps/electricitymaps-contrib" alt="Electricity Maps is released under the GNU-AGPLv3 license." /></a>
  p>

![image](.github/images/electricity-maps-banner.png#gh-light-mode-only)
![image](.github/images/electricity-maps-banner-dark.png#gh-dark-mode-only)

## Introduction

This project aims to provide a free, open-source, and transparent visualisation of the electricity data around the world.

We fetch the raw production data from public, free, and official sources. They include official government and transmission system operators' data. We then run [our flow-tracing algorithm](https://www.electricitymaps.com/blog/flow-tracing), estimation models, forecast engine and much more to calculate the most accurate view of how electricity consumption changes over time for each country.

_Try it out at [app.electricitymaps.com](https://app.electricitymaps.com), or download the app on [Google Play](https://play.google.com/store/apps/details?id=com.tmrow.electricitymap&utm_source=github) or [App store](https://itunes.apple.com/us/app/electricity-map/id1224594248&utm_source=github)._

## Contributing

The Electricity Maps app is a community project and we welcome contributions from anyone!

We are always looking for help to build parsers for new countries, fix broken parsers, improve accuracy of data sources, discuss new potential data sources, update region capacities, and much more.

Read our [contribution guidelines](/CONTRIBUTING.md) to get started.

## Community & Support

Use these channels to be part of the community, ask for help while using Electricity Maps, or just learn more about what's going on:

- [GitHub Issues](https://github.com/electricitymaps/electricitymaps-contrib/issues): Raise any issues you encounter with the data or bugs you find while using the app.
- [GitHub Discussions](https://github.com/electricitymaps/electricitymaps-contrib/discussions): Join discussions and share new ideas for features.
- [GitHub Wiki](https://github.com/electricitymaps/electricitymaps-contrib/wiki): Learn more about methodology, guides for how to set up development environment, etc.
- [Our Commercial Website](https://electricitymaps.com/): Learn more about how you or your company can use the data too.
- [Our Blog](https://electricitymaps.com/blog/): Read about the green transition and how Electricity Maps is helping to accelerate it.
- [Twitter](https://twitter.com/electricitymaps): Follow for latest news
- [LinkedIn](https://www.linkedin.com/company/electricitymaps): Follow for latest news

## License

This repository is licensed under GNU-AGPLv3 since v1.5.0, find our license [here](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE.md). Contributions prior to commit [cb9664f](https://github.com/electricitymaps/electricitymaps-contrib/commit/cb9664f43f0597bedf13e832047c3fc10e67ba4e) were licensed under [MIT license](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE_MIT.txt)

## Frequently asked questions

**Where does the data come from?**
The data comes from many different sources. You can check them out [here](https://github.com/electricityMaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md)

**Why do you calculate the carbon intensity of _consumption_?**
In short, citizens should not be responsible for the emissions associated with all the products they export, but only for what they consume.
Consumption-based accounting (CBA) is a very important aspect of climate policy and allows assigning responsibility to consumers instead of producers.
Furthermore, this method is robust to governments relocating dirty production to neighboring countries in order to green their image while still importing from it.
You can read more in our blog post [here](https://electricitymaps.com/blog/flow-tracing/).

**Why don't you show emissions per capita?**
A country that has few inhabitants but a lot of factories will appear high on CO<sub>2</sub>/capita.
This means you can "trick" the numbers by moving your factory abroad and import the produced _good_ instead of the electricity itself.
That country now has a low CO<sub>2</sub>/capita number because we only count CO<sub>2</sub> for electricity (not for imported/exported goods).
The CO<sub>2</sub>/capita metric, by involving the size of the population, and by not integrating all CO<sub>2</sub> emission sources, is thus an incomplete metric.
CO<sub>2</sub> intensity on the other hand only describes where is the best place to put that factory (and when it is best to use electricity), enabling proper decisions.

**CO<sub>2</sub> emission factors look high — what do they cover exactly?**
The carbon intensity of each type of power plant takes into account emissions arising from the whole life cycle of the plant (construction, fuel production, operational emissions and decommissioning). Read more on the [Emissions Factor Wiki page](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors).

**How can I get access to the live API?**
All this and more can be found **[here](https://electricitymaps.com/)**.
You can also visit our **[data portal](https://www.electricitymaps.com/data-portal)** to download historical datasets.

**Is the map frontend open source?**
In the past, the map frontend was open source, but we have since rewritten the app completely and moved it to our own platform in order to expand the available features and provide a consistent user experience across our product offerings.
