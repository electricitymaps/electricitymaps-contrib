# Welcome! 🎉

Welcome to the Electricity Maps open source contribution repository. </br>
Any and all contributions however big or small are welcome.

# Links

- [README][readme]
- [Code of Conduct][code of conduct]
- [License][license]
- [Wiki][wiki]

# Code of Conduct

This repository and by extension its community have adopted the [Contributor Covenant][contributor covenant] v2.1 as its code of conduct.
If you have any questions about the code of conduct or feel the need to report an incident you can do so by emailing us at codeofconduct@electricitymaps.com. For the full code of conduct see [CODE_OF_CONDUCT.md][code of conduct].

# License

We use the GNU Affero General Public License v3.0 for this repository, check the [LICENSE.md][license] file details about what exactly this entails. Contributions prior to commit [cb9664f][commit cb9664f] where licensed under [MIT license][old_license]

# Getting Started

## Non-code contributions

There are several ways to help out without coding, these are primarily:

- Opening issues for bugs.
- Opening issues for data problems.
- Opening and/or participating in discussions about new data sources, features, and more.
- Opening issues when capacity data sources have been updated or changed.
- Finding new data sources, wiki page: [Find data sources][wiki find data sources]
- Verify existing data sources, wiki page: [Verify data sources][wiki verify data sources]
- Adding new or updating our existing translations, wiki page: [Translating app.electricitymaps.com][wiki translating the app]
- And more!

> **Note**
> Take a look at the wiki pages for more detailed instructions

## Zone and exchange configurations

Static information about zones and exchanges are located at [config/zones][config zones] and [config/exchanges][config exchanges] respectively.
The zone configurations hold information such as the installed capacity, which parsers to use, fallback mixes, contributors and other keys that are required by our frontend and internal systems; and while similar the exchange configs hold the location, capacity, direction and parsers required.

## Parser guidelines

To get started with editing the parsers use the following steps:

1. Run `uv sync --extra parsers` to install all needed dependencies.
2. Use `uv run test_parser ZONE_KEY` to test any parser changes.

Note: This requires you to have [Python 3.10][python homepage] and [uv][uv homepage] installed, you can see their respective installation guides here:

- [Downloading Python][python install guide]
- [uv installation][uv install guide]

### Parser information

For more detailed information about parsers specifically you can look at the parser [README][parser readme] located at [electricitymap/contrib/parsers/README.md][parser readme] with specific information about the parser functions located in the [electricitymap/contrib/parser/example][parser examples folder] folder

#### Example parser:

For an example of how a parser can look we have an example here: </br> [electricitymap/contrib/parsers/examples/example_parser.py][example parser]

### Formatting the parsers

We use [black][black homepage] and [isort][isort homepage] as code formatters for python which is automatically checked in the CI job `Python / Formatting`.

If this jobs fails and you need to manually format the code you can run `uv run format` in the top level of the repository.

Check the [wiki page][wiki python code formatting] for more details and tips.

## Front-end guidelines

To get started with editing the frontend use the following steps:

1. Use `cd web` to go into the web directory
2. Then use `pnpm install` to get all dependencies installed.

Note: This requires you to have [node.js][node homepage] and [pnpm][pnpm homepage] installed, you can see their respective installation guides here:

- [How to install node.js][node installation guide]
- [pnpm installation][pnpm installation guide]

### Frontend structure

The frontend can be broken down into 2 main parts, the web app built [Vite][vitejs] and the mobile app built with [capacitor][capacitorjs].
Both of these share a common code base that is built upon [react][reactjs].

As a result we have a frontend folder structure that looks like this:

```
mobileapp
├── android
├── assets
├── icons
└── ios
web
├── config
├── cypress
├── geo
├── public
├── scripts
└── src
    ├── api
    ├── components
    ├── features
    ├── hooks
    ├── stories
    ├── testing
    ├── translation
    └── utils
```

### State management

We use [Jotai][jotai homepage] that saves our state in primitive atoms, these live in [web/src/utils/state/atoms.ts][jotai atoms] and are then imported in the individual frontend files where it's needed. If you have a need to save the state for a new feature you should add a new atom to this file so we keep everything organized.

### Formatting the frontend

The frontend uses [ESLint][eslint homepage] and [Prettier][prettier homepage] as formatters for all code and this is automatically checked in the CI jobs `Prettier / Check` and `ESLint / Check`.

If these jobs fail and you need to format the code you can run `yarn lint --fix` in the `/web` folder to do so.

Check the [wiki page][wiki js code formatting] on formatting for more details and tips.

# Contribution lifecycle

In order for your PR to be accepted and deployed it will need to pass a series of checks, these checks will be defined and explained in the following section of this document.

## Overview

```mermaid
%%{init: {"flowchart": {"defaultRenderer": "elk"}} }%%
flowchart LR
    subgraph idContrib["Electricity Maps contrib"]
    direction LR
        id1((Open a PR))
        id2{First time contributor?}
        id3(Await EMaps team CI approval)
        id4{Is the CI tests passing?}
        id5(Make changes)
        id6{Passing review from EMaps team member}
        id7(PR is merged)
        id8(Deployed to Staging)
        id1-->id2
        id2-->|Yes|id3
        id2-->|No|id4
        id3-->id4
        id4-->|No|id5
        id5-->id4
        id4-->|Yes|id6
        id6-->|No|id5
        id6-->|Yes|id7
        id7-->id8
    end
    subgraph idInternal["Electricity Maps internal"]
    direction LR
        id9((Automatic PR created))
        id10{Are internal CI tests passing}
        id11(Make changes)
        id12{Passing review from Emaps member?}
        id13(Deployed to production)
        id9-->id10
        id10-->|No|id11
        id11-->id10
        id10-->|Yes|id12
        id12-->|No|id11
        id12-->|Yes|id13
    end
    id7-->id9
```

## Description

In order to do code changes to the Electricity Maps repository you need to fork the repo and make changes in your own fork and then open a pull request (PR) against the Electricity Maps repository.

Once this has been done the automatic and manual review process starts, this consists of manual approval of the CI pipeline if you are a first time contributor, if the CI pipeline passes a team member will review your specific code changes. If they pass all automated tests and manual review from a Electricity Maps Employee it will be merged in our contrib PR. This does not mean it will be automatically de deployed or that the changes will be instantly visible.

If it is frontend changes it will be deployed to our staging environment at https://staging.electricitymaps.com and if there is parser changes these go on to more internal tests that includes both automated test suits and manual reviews. Once everything passes and an approval has been granted a new release will be created that updates the production environment for both the frontend and parser changes.

<!-- Link definitions to keep the text clean -->

[uv homepage]: https://github.com/astral-sh/uv
[python homepage]: https://www.python.org/
[python install guide]: https://wiki.python.org/moin/BeginnersGuide/Download
[uv install guide]: https://docs.astral.sh/uv/getting-started/installation/
[example parser]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/electricitymap/contrib/parsers/examples/example_parser.py
[black homepage]: https://github.com/psf/black
[isort homepage]: https://pycqa.github.io/isort/
[wiki python code formatting]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Format-your-code-contribution#python-code-formatting
[node homepage]: https://nodejs.org/
[pnpm homepage]: https://pnpm.io/
[node installation guide]: https://nodejs.org/en/learn/getting-started/how-to-install-nodejs
[pnpm installation guide]: https://pnpm.io/installation
[jotai homepage]: https://jotai.org/
[jotai atoms]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/web/src/utils/state/atoms.ts
[eslint homepage]: https://eslint.org/
[prettier homepage]: https://prettier.io/
[wiki js code formatting]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Format-your-code-contribution#js-code-formatting
[wiki translating the app]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Translating-app.electricitymaps.com
[reactjs]: https://reactjs.org/
[vitejs]: https://vitejs.dev/
[capacitorjs]: https://capacitorjs.com/
[readme]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/README.md
[code of conduct]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/CODE_OF_CONDUCT.md
[license]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE.md
[wiki]: https://github.com/electricitymaps/electricitymaps-contrib/wiki
[wiki find data sources]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Find-data-sources
[wiki verify data sources]: https://github.com/electricitymaps/electricitymaps-contrib/wiki/Verify-data-sources
[contributor covenant]: https://www.contributor-covenant.org/
[commit cb9664f]: https://github.com/electricitymaps/electricitymaps-contrib/commit/cb9664f43f0597bedf13e832047c3fc10e67ba4e
[old_license]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/LICENSE_MIT.txt
[config zones]: https://github.com/electricitymaps/electricitymaps-contrib/tree/master/config/zones
[config exchanges]: https://github.com/electricitymaps/electricitymaps-contrib/tree/master/config/exchanges
[parser readme]: https://github.com/electricitymaps/electricitymaps-contrib/tree/master/parsers/README.md
[parser examples folder]: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/electricitymap/contrib/parsers/examples/
