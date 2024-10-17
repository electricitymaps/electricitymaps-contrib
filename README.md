<p align="center">
  <a href="https://app.electricitymaps.com">
    <img alt="Electricity Maps" src="https://raw.githubusercontent.com/electricitymaps/electricitymaps-contrib/master/web/public/images/electricitymaps-icon.svg" width="100" />
  </a>
</p>
<h1 align="center">
  Electricity Maps
</h1>

<p align="center">
A real-time and historical visualisation of the Greenhouse Gas Intensity (in terms of CO<sub>2</sub> equivalent) of electricity production and consumption worldwide.<br>
  <strong><a href="https://app.electricitymaps.com">Explore the App »</a></strong>
</p>

<p align="center">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/electricitymaps/electricitymaps-contrib">
  <a href="https://github.com/electricitymaps/electricitymaps-contrib/releases">
    <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/electricitymaps/electricitymaps-contrib"></a>
  <a href="https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE.md">
    <img alt="License" src="https://img.shields.io/github/license/electricitymaps/electricitymaps-contrib" /></a>
  <a href="https://slack.electricitymaps.com">
    <img alt="Join our Slack" src="https://img.shields.io/badge/slack-3700%2B-%23126945" /></a>
  <a href="https://twitter.com/intent/follow?screen_name=ElectricityMaps">
    <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/ElectricityMaps" /></a>
</p>

![Electricity Maps](web/public/images/electricitymap_social_image.png#gh-light-mode-only)
![Electricity Maps](web/public/images/electricitymap_social_image_dark.png#gh-dark-mode-only)

## Overview

**Electricity Maps** is an open-source project providing a transparent, real-time visualization of the carbon intensity of electricity **consumption** across the globe. The platform processes raw data from public, official sources (government bodies, Transmission System Operators, etc.) to calculate a region's carbon intensity using [our flow-tracing algorithm](https://www.electricitymaps.com/blog/flow-tracing).

**Get started** by exploring our live application at [app.electricitymaps.com](https://app.electricitymaps.com), or download our mobile app from [Google Play](https://play.google.com/store/apps/details?id=com.tmrow.electricitymap&utm_source=github) or the [App Store](https://itunes.apple.com/us/app/electricity-map/id1224594248&utm_source=github).

## Contributing to the Project

Electricity Maps thrives on community collaboration. We welcome contributions in areas such as:

- **Building new data parsers** for additional countries and regions.
- **Maintaining or fixing existing parsers**.
- Enhancing the **frontend user interface** for better visualizations.
- Improving **data accuracy** and adding new **data sources**.
- Updating **regional capacities** for accurate flow-tracing.
- **Discussing feature ideas** and proposing enhancements.

Check out our [Contribution Guidelines](/CONTRIBUTING.md) to learn how to get involved and where your expertise can make an impact.

### Setting Up a Development Environment

To contribute to the project, you’ll first need to set up a local development environment. You can find detailed instructions in our [GitHub Wiki](https://github.com/electricitymaps/electricitymaps-contrib/wiki). This guide includes information on:

- Installing the necessary dependencies (Node.js, Python, etc.)
- Working with the data parsers and flow-tracing algorithm.
- Setting up the web or mobile frontend environment.

If you need help, feel free to join our community channels or raise a GitHub issue.

## Data Sources & Methodology

We collect raw electricity production and consumption data from a variety of **public, official** sources such as **government websites**, **transmission operators**, and other open APIs. Data sources for each country and region are documented [here](https://github.com/electricityMaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md).

### Why Consumption-Based Carbon Intensity?
We calculate the **carbon intensity of electricity consumption**, not production. This means we assign the emissions to the consumers of electricity rather than the producers. It prevents greenwashing, where governments relocate polluting industries while still importing their energy.

Read more about the importance of **Consumption-Based Accounting (CBA)** in our [blog post](https://electricitymaps.com/blog/flow-tracing/).

### Data Accuracy & Emission Factors
The carbon intensity figures account for **full lifecycle emissions**, including the construction, operation, and decommissioning of power plants. More details on this methodology are available on the [Emission Factors Wiki page](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors).

## Community & Support

We encourage you to join our growing developer community to ask questions, share your ideas, or showcase your work:

- **[Slack Community](https://slack.electricitymaps.com)**: A lively space where developers and contributors discuss ongoing projects and receive feedback.
- **[GitHub Issues](https://github.com/electricitymaps/electricitymaps-contrib/issues)**: Report bugs, suggest improvements, or request new features.
- **[GitHub Discussions](https://github.com/electricitymaps/electricitymaps-contrib/discussions)**: Collaborate and brainstorm with other developers.
- **[FAQ](https://app.electricitymaps.com/FAQ)**: Find answers to common questions.
- **[GitHub Wiki](https://github.com/electricitymaps/electricitymaps-contrib/wiki)**: Deep dive into our technical methodology, development guides, and more.

## Accessing Historical Data & API

Want to integrate carbon intensity data into your project? We provide an API for both real-time and historical data. Learn more about accessing it via our **[Data Portal](https://www.electricitymaps.com/data-portal)**.

For commercial access or large-scale use cases, visit our **[Commercial Website](https://electricitymaps.com/)** for information on tailored solutions.

## License

This project is licensed under the **GNU-AGPLv3** license since version 1.5.0. You can find the full license [here](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE.md). Contributions prior to commit [cb9664f](https://github.com/electricitymaps/electricitymaps-contrib/commit/cb9664f43f0597bedf13e832047c3fc10e67ba4e) were licensed under the [MIT License](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE_MIT.txt).

## Get Involved

Whether you're fixing bugs, improving our data models, or suggesting a new feature, we encourage developers to contribute to **Electricity Maps** and make a real-world impact in accelerating the transition to greener electricity.

### Start Contributing:
- Fork the repository.
- Install dependencies as outlined in the [Contribution Guidelines](https://github.com/electricitymaps/electricitymaps-contrib/blob/master/CONTRIBUTING.md).
- Start building! We look forward to your contributions.
