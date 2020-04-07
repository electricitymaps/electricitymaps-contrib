import { isEmpty } from 'lodash';
import { useLocation } from 'react-router-dom';
import { createBrowserHistory } from 'history';

import thirdPartyServices from '../services/thirdparty';
import { dispatch } from '../store';

// TODO: Replace this with React Router DOM
// `useHistory` hook after full migration to React.
export const history = createBrowserHistory();

function pushToHistory({ pathname, search }) {
  // Push the new URL state to browser history and track
  // it only if the new URL differs from the current one
  const url = `${pathname}${search}`;
  if (url !== `${history.location.pathname}${history.location.search}`) {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: url });
    }
    history.push(url);
  }
}

export function navigateToPath(pathname) {
  // Preserve search params when navigating between pages
  pushToHistory({ pathname, search: history.location.search });
}

//
// Search params
//

export function useSearchParams() {
  return new URLSearchParams(useLocation().search);
}

export function useCustomDatetime() {
  return useSearchParams().get('datetime');
}

export function useRemoteEndpoint() {
  return useSearchParams().get('remote') === 'true';
}

export function useSolarEnabled() {
  return useSearchParams().get('solar') === 'true';
}

export function useWindEnabled() {
  return useSearchParams().get('wind') === 'true';
}

// TODO: Deprecate in favor of useSearchParams (requires move to React)
function getSearchParams() {
  return new URLSearchParams(history.location.search);
}

// TODO: Deprecate in favor of React Router useParams (requires move to React)
export function getCurrentPage() {
  return history.location.pathname.split('/')[1];
}

// TODO: Deprecate in favor of React Router useParams (requires move to React)
export function getZoneId() {
  return history.location.pathname.split('/')[2];
}

// TODO: Deprecate in favor of useCustomDatetime (requires move to React)
export function getCustomDatetime() {
  return getSearchParams().get('datetime');
}

// TODO: Deprecate in favor of useRemoteEndpoint (requires move to React)
export function isRemoteEndpoint() {
  return getSearchParams().get('remote') === 'true';
}

// TODO: Deprecate in favor of useSolarEnabled (requires move to React)
export function isSolarEnabled() {
  return getSearchParams().get('solar') === 'true';
}

// TODO: Deprecate in favor of useWindEnabled (requires move to React)
export function isWindEnabled() {
  return getSearchParams().get('wind') === 'true';
}

function updateSearchParams(searchParams) {
  let search = searchParams.toString();
  if (search) {
    search = `?${search}`;
  }
  // Keep the pathname intact when updating search params
  pushToHistory({ pathname: history.location.pathname, search });
}

// TODO: Move this logic in the solar button once the React component is there
// See https://github.com/tmrowco/electricitymap-contrib/issues/2345.
export function setSolarEnabled(solarEnabled) {
  const searchParams = getSearchParams();
  if (solarEnabled) {
    searchParams.set('solar', true);
  } else {
    searchParams.delete('solar');
  }
  updateSearchParams(searchParams);
}

// TODO: Move this logic in the wind button once the React component is there
// See https://github.com/tmrowco/electricitymap-contrib/issues/2345.
export function setWindEnabled(windEnabled) {
  const searchParams = getSearchParams();
  if (windEnabled) {
    searchParams.set('wind', true);
  } else {
    searchParams.delete('wind');
  }
  updateSearchParams(searchParams);
}

//
// Redux state sync
//

function updateStateFromURL() {
  dispatch({
    type: 'UPDATE_STATE_FROM_URL',
    payload: {
      customDatetime: getCustomDatetime(),
      currentPage: getCurrentPage(),
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
