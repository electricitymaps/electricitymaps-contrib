# Welcome! 🎉

Welcome to the Electricity Maps open source contribution repository. </br>
Any and all contributions however big or small are welcome.

# Contribution Guidelines

## Non-code contributions

There are several ways to help out without coding, these are primarily:

- Opening issues for bugs.
- Opening issues for data problems.
- Opening and/or participating in discussions about new data sources, features, and more.
- Opening issues when capacity data sources have been updated or changed.
- And more!

## Parser guidelines

To get stated with editing the parsers use the following steps:

1. Run `poetry install -E parsers` to install all needed dependencies.
2. Use `poetry run test_parser ZONE_KEY` to test any parser changes.

Note: This requires you to have [Python][python homepage] and [Poetry][poetry homepage] installed, you can see their respective installation guides here:

- [Downloading Python][python install guide]
- [poetry installation][poetry install guide]

### Parser requirements

There are no clear cut model or template that works for all parsers as all data are different and unique but there are some basic requirements all parsers need to follow:

- They need to return valid data from a credible source.
- They need to return the date for when the data was collected together with the data.
- They need to return at least one valid Electricity Maps data object (production, consumption, exchange, price, etc).

#### Example parser:

For a example on how a parser can look we have an example here: </br> [parsers/example.py][example parser]

### Formatting the parsers

We use [black][black homepage] and [isort][isort homepage] as code formatters for python which is automatically checked in the CI job `Python / Formatting`.

If this jobs fail and you need to manually format the code you can run `poetry run format` in the top level of the repository.

Check the [wiki page][wiki python code formatting] for more details and tips.

## Front-end guidelines

To get started with editing the fronted use the following steps:

1. Use `cd web` to go into the web directory
2. Then use `pnpm install` to get all dependencies installed.

Note: This requires you to have [node.js][node homepage] and [pnpm][pnpm homepage] installed, you can see there respective installation guides here:

- [How to install node.js][node installation guide]
- [pnpm installation][pnpm installation guide]

### Frontend structure

### State management

We use [Jotai][jotai homepage] that saves our state in primitive atoms, these live in #TODO: LINK TO ATOM FILE WHEN REWRITE IS MERGED and are then imported in the individual frontend files where it's needed. If you have a need to save the state for a new feature you should add a new atom to this file so we keep everything organized.

### Formatting the frontend

The frontend uses [ESLint][eslint homepage] and [Prettier][prettier homepage] as formatters for all code and this is automatically checked in the CI jobs `Prettier / Check` and `ESLint / Check`.

If these jobs fail and you need to format the code you can run `yarn lint --fix` in the `/web` folder to do so.

Check the [wiki page][wiki js code formatting] on formatting for more details and tips.

<!-- Link definitions to keep the text clean -->
[poetry homepage]: https://python-poetry.org/
[python homepage]: https://www.python.org/
[python install guide]: https://wiki.python.org/moin/BeginnersGuide/Download
[poetry install guide]: https://python-poetry.org/docs/#installation
[example parser]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/parsers/example.py
[black homepage]: https://github.com/psf/black
[isort homepage]: https://pycqa.github.io/isort/
[wiki python code formatting]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Format-your-code-contribution#python-code-formatting
[node homepage]: https://nodejs.org/
[pnpm homepage]: https://pnpm.io/
[node installation guide]: https://nodejs.dev/en/learn/how-to-install-nodejs/
[pnpm installation guide]: https://pnpm.io/installation
[jotai homepage]: https://jotai.org/
[eslint homepage]: https://eslint.org/
[prettier homepage]: https://prettier.io/
[wiki js code formatting]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Format-your-code-contribution#js-code-formatting
