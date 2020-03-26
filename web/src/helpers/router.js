import { isEmpty } from 'lodash';
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

export function updateURLFromState(state) {
  const {
    currentPage,
    customDate,
    selectedZoneName,
    solarEnabled,
    useRemoteEndpoint,
    windEnabled,
  } = state.application;

  // Build search params from application state, ignoring falsey values
  const searchParams = Object.assign({},
    customDate ? { datetime: customDate } : {},
    solarEnabled ? { solar: solarEnabled } : {},
    useRemoteEndpoint ? { remote: useRemoteEndpoint } : {},
    windEnabled ? { wind: windEnabled } : {});

  // Build the URL string
  let url = `/${currentPage}`;
  if (selectedZoneName) {
    url += `/${selectedZoneName}`;
  }
  if (!isEmpty(searchParams)) {
    url += `?${(new URLSearchParams(searchParams)).toString()}`;
  }

  // Push the new URL state to browser history and track
  // it only if the new URL differs from the current one
  if (url !== `${history.location.pathname}${history.location.search}`) {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: url });
    }
    history.push(url);
  }
}

export function navigateToURL(pathname) {
  if (pathname !== history.location.pathname) {
    const url = `${pathname}${history.location.search}`;
    history.push(url);
  }
}
