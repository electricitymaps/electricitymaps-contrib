# Welcome! 🎉

Welcome to the Electricity Maps open source contribution repository. </br>
Any and all contributions however big or small are welcome.

# Contribution Guidelines

## Non-code contributions

## Parser guidelines

### Parser requirements

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
