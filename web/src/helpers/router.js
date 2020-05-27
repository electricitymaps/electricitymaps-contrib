import { createBrowserHistory, createHashHistory } from 'history';

// Use BrowserHistory in the web browser and HashHistory
// in the mobile apps as we need to keep relative resource
// paths for the mobile which are fundamentally incompatible
// with browser side URL paths routing.
// TODO: Replace this with React Router DOM
// `useHistory` hook after full migration to React.
export const history = window.isCordova ? createHashHistory() : createBrowserHistory();

// TODO: Deprecate in favor of React Router useParams (requires move to React)
export function getZoneId() {
  return history.location.pathname.split('/')[2];
}

// TODO: Get rid of this when a better system is put in place for switching languages.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2382.
export function hideLanguageSearchParam() {
  const searchParams = new URLSearchParams(history.location.search);
  searchParams.delete('lang');
  history.replace(`?${searchParams.toString()}`);
}
hideLanguageSearchParam();
