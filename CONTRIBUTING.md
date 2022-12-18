# Welcome! 🎉

Welcome to the Electricity Maps open source contribution repository. </br>
Any and all contributions however big or small are welcome.

# Contribution Guidelines

## Non-code contributions

There are several ways to help out without coding, these are primarily:

- Opening issues for bugs.
- Opening issues for data issues.
- Opening and participating in discussions about new data sources.
- Opening issues when capacity data sources have been updated or changed.
- And more!

## Parser guidelines

### Parser requirements

There are no clear cut model or template that works for all parsers as all data are different and unique but there are some basic requirements all parsers need to follow:

- They need to return valid data from a credible source.
- They need to return the date for when the data was collected together with the data.
- They need to return at least one valid Electricity Maps data object (production, consumption, exchange, price, etc).

<!-- TODO: Add link to or create and link to a clear parser/data type documentation -->

### Formatting the parsers

The parsers uses black and isort as code formatters which is automatically checked in the CI job `Python / Formatting`.

If this jobs fail and you need to manually format the code you can run `poetry run format` in the top level of the repository.

Check the [wiki page](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Format-your-code-contribution#python-code-formatting) for more details and tips.

## Front-end guidelines

### Frontend structure

### State management

### Formatting the frontend

The frontend uses ESLint and Prettier as formatters for all code and this is automatically checked in the CI jobs `Prettier / Check` and `ESLint / Check`.

If these jobs fail and you need to format the code you can run `yarn lint --fix` in the `/web` folder to do so.

Check the [wiki page](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Format-your-code-contribution#js-code-formatting) on formatting for more details and tips.
