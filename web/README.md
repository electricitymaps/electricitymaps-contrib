# Electricity Maps

**This documentation is specifically for the frontend web/mobile app.**

_If you're looking for more info on the parsers, check out [how to setup Python development environment](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Set-up-local-environment#setup-python-development-environment) and [how to fix a broken parser (and test it locally)](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Fixing-a-broken-parser)._

## Local development

Prerequisites:

- Ensure you have `NodeJS` and `pnpm` installed locally (`brew install pnpm`)
- Run `pnpm install` in both the web and mockserver directories

1. Start the mockserver: `pnpm run mockserver`
2. Run app in another tab: `pnpm dev`

## Scripts

- `pnpm mockserver` - starts the mockserver.
- `pnpm dev` - start a development server with hot reload.
- `pnpm build` - build for production. The generated files will be in the `dist` folder.
- `pnpm preview` - locally preview the production build.
- `pnpm test` - run unit and integration tests related to changed files based on git.
- `pnpm cy:e2e` - work with integration tests. Remember to run `pnpm dev` before!
- `pnpm cy:components` - work with component tests.
  <!-- - `pnpm test:ci` - run all unit and integration tests in CI mode. -->
  <!-- - `pnpm test:e2e` - run all e2e tests with the Cypress Test Runner. -->
  <!-- - `pnpm test:e2e:headless` - run all e2e tests headlessly. -->
- `pnpm format` - format all files with Prettier.
- `pnpm lint` - runs TypeScript and ESLint.
- `pnpm validate` - runs `lint`, `test:ci` and `test:e2e:ci`.

### TODO: Scripts currently disabled until we're ready

```
    "test:e2e": "pnpm preview:test 'cypress open'",
    "test:e2e:headless": "pnpm preview:test 'cypress run'",
    "test:e2e:ci": "vite build && pnpm preview:test 'cypress run --record'",
```

### Using production API (internal eMap team only)

As an eMap internal team member, you can also run the app connected to production API instead of the mockserver:

- Run `VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN='YOUR TOKEN' pnpm dev`
- Add a `?remote=true` query parameter

### Building for production

- Add an environment variable for `SENTRY_AUTH_TOKEN="find it here => https://sentry.io/settings/account/api/auth-tokens/"`
- Add an environment variable for `VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN='YOUR TOKEN'`

## Geometries development

See [how to edit world geometries](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Edit-world-geometries).

## Icon usage

We use [react-icons](https://github.com/react-icons/react-icons) and by default the app uses the "Heroicons 2" library with "Outline" variants.

If an icon should be missing, then feel free to look into other libraries to find an icon that matches the style. An important rule here is that we ideally want to use only outlined icons (and no filled/solid icons).

Search for icons here: [https://react-icons.github.io/react-icons/](https://react-icons.github.io/react-icons/)

## State Management

We use [jotai](https://jotai.org/) for global UI state management, [TanStack Query](https://tanstack.com/query/v4/docs/overview) for data state management and React's setState() for local component state.

### Do I have to put all my state into jotai? Should I ever use React's setState()?

> There is no “right” answer for this. Some users prefer to keep every single piece of data in jotai, to maintain a fully serializable and controlled version of their application at all times. Others prefer to keep non-critical or UI state, such as “is this dropdown currently open”, inside a component's internal state. (Original [link](https://redux.js.org/faq/organizing-state#do-i-have-to-put-all-my-state-into-redux-should-i-ever-use-reacts-setstate), visited 2022)

The following list can be used to determine whether to store in atom or setState.

- Do other parts of the application care about this data?
- Do you need to be able to create further derived data based on this original data?
- Is the same data being used to drive multiple components?
- Do you want to persist the data for another session?
- Do you want to cache the data (ie, use what's in state if it's already there instead of re-requesting it)?

**Choosing atoms**

1. States that drastically changes the behavior of the map and is important when sharing with other people. Examples could be production/consumption and country/zones view. This state should be stored in the URL and localstorage. Use atomWithCustomStorage.

2. States that personalizes the app but is not essential to be shared. For example dark-mode and color-blind mode. This state should be stored in localstorage. use atomWithStorage

3. State that changes the viewer experience and may be disrupted by a reload but is not essential to be shared. This state should be stored in sessionStorage. Use atomWithStorage.

4. All other global state should be able to use the basic atom.

**Avoid prop drilling with global state**

In general all global atoms should be accessed through useAtom and not through prop drilling. This allows our components to be more modular and takes full advantage of the global nature of atoms. In general we want to avoid transporting props multiple levels down.

If the components are very closely related it may make sense to pass down derived values instead.

- ButtonGroup.tsx
- Button1.tsx
- Button2.tsx
- Button3.tsx

Here the buttonGroup may retrieve a state 'globalSelectedValue' from the global state. Instead of passing down 'globalSelectedValue' to the buttons, the buttonGroup can pass down a 'isSelected' boolean prop which depends on 'globalSelectedValue' and the value of the individual buttons.
