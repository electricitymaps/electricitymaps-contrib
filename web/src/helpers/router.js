import { createBrowserHistory, createHashHistory } from 'history';

import { dispatch } from '../store';

// Use BrowserHistory in the web browser and HashHistory
// in the mobile apps as we need to keep relative resource
// paths for the mobile which are fundamentally incompatible
// with browser side URL paths routing.
// TODO: Replace this with React Router DOM
// `useHistory` hook after full migration to React.
export const history = window.isCordova ? createHashHistory() : createBrowserHistory();

// TODO: Deprecate in favor of useSearchParams (requires move to React)
function getSearchParams() {
  return new URLSearchParams(history.location.search);
}

// TODO: Deprecate in favor of React Router useParams (requires move to React)
export function getZoneId() {
  return history.location.pathname.split('/')[2];
}

// TODO: Deprecate in favor of useCustomDatetime (requires move to React)
export function getCustomDatetime() {
  return getSearchParams().get('datetime');
}

// TODO: Deprecate in favor of useSolarEnabled (requires move to React)
export function isSolarEnabled() {
  return getSearchParams().get('solar') === 'true';
}

// TODO: Deprecate in favor of useWindEnabled (requires move to React)
export function isWindEnabled() {
  return getSearchParams().get('wind') === 'true';
}

// TODO: Get rid of this when a better system is put in place for switching languages.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2382.
export function hideLanguageSearchParam() {
  const searchParams = getSearchParams();
  searchParams.delete('lang');
  history.replace(`?${searchParams.toString()}`);
}
hideLanguageSearchParam();

// TODO: Remove once we don't need the copy of URL state in the Redux state anymore
// See https://github.com/tmrowco/electricitymap-contrib/issues/2296.
function updateStateFromURL() {
  dispatch({
    type: 'UPDATE_STATE_FROM_URL',
    payload: {
      customDatetime: getCustomDatetime(),
      selectedZoneName: getZoneId(),
      solarEnabled: isSolarEnabled(),
      windEnabled: isWindEnabled(),
    },
  });
}

// Update Redux state with the URL search params initially and also
// every time the URL change is triggered by a browser action to ensure
// the URL -> Redux binding (the other direction is ensured by observing
// the relevant state Redux entries and triggering the URL update below).
updateStateFromURL();
history.listen(() => {
  updateStateFromURL();
});
