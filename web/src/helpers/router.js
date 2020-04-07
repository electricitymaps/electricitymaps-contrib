import { isEmpty } from 'lodash';
import { useLocation } from 'react-router-dom';
import { createBrowserHistory } from 'history';

import thirdPartyServices from '../services/thirdparty';
import { dispatch } from '../store';

// TODO: Replace this with React Router DOM
// `useHistory` hook after full migration to React.
export const history = createBrowserHistory();

// Update Redux state with the URL search params initially and also
// every time the URL change is triggered by a browser action to ensure
// the URL -> Redux binding (the other direction is ensured by observing
// the relevant state Redux entries and triggering the URL update below).
dispatch({ type: 'UPDATE_STATE_FROM_URL', payload: { url: window.location } });
history.listen(() => {
  dispatch({ type: 'UPDATE_STATE_FROM_URL', payload: { url: window.location } });
});

function pushURL(url) {
  // Push the new URL state to browser history and track
  // it only if the new URL differs from the current one
  if (url !== `${history.location.pathname}${history.location.search}`) {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: url });
    }
    history.push(url);
  }
}

function useSearchParams() {
  return new URLSearchParams(useLocation().search);
}

export function useSolarEnabled() {
  return useSearchParams().get('solar') === 'true';
}

export function useWindEnabled() {
  return useSearchParams().get('wind') === 'true';
}

function getSearchParams() {
  return new URLSearchParams(history.location.search);
}

export function getCustomDatetime() {
  return getSearchParams().get('datetime');
}

export function isRemoteEndpoint() {
  return getSearchParams().get('remote') === 'true';
}

export function isSolarEnabled() {
  return getSearchParams().get('solar') === 'true';
}

export function isWindEnabled() {
  return getSearchParams().get('wind') === 'true';
}

function setSearchParams(searchParams) {
  let search = searchParams.toString();
  if (search) {
    search = `?${search}`;
  }
  pushURL(`${history.location.pathname}${search}`);
}

export function setSolarEnabled(solarEnabled) {
  const searchParams = getSearchParams();
  if (solarEnabled) {
    searchParams.set('solar', true);
  } else {
    searchParams.delete('solar');
  }
  setSearchParams(searchParams);
}

export function setWindEnabled(windEnabled) {
  const searchParams = getSearchParams();
  if (windEnabled) {
    searchParams.set('wind', true);
  } else {
    searchParams.delete('wind');
  }
  setSearchParams(searchParams);
}

export function navigateToURL(pathname) {
  pushURL(`${pathname}${history.location.search}`);
}

export function updateURLFromState(state) {
  const {
    currentPage,
    customDatetime,
    selectedZoneName,
    solarEnabled,
    windEnabled,
  } = state.application;

  // Build search params from application state, ignoring falsey values
  const searchParams = Object.assign({},
    customDatetime ? { datetime: customDatetime } : {},
    solarEnabled ? { solar: solarEnabled } : {},
    isRemoteEndpoint() ? { remote: isRemoteEndpoint() } : {},
    windEnabled ? { wind: windEnabled } : {});

  // Build the URL string
  let url = '';
  if (currentPage) {
    url += `/${currentPage}`;
  }
  if (selectedZoneName) {
    url += `/${selectedZoneName}`;
  }
  if (!isEmpty(searchParams)) {
    url += `?${(new URLSearchParams(searchParams)).toString()}`;
  }

  // Push the URL to history
  pushURL(url);
}
