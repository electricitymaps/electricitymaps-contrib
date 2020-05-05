import React, { useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { createBrowserHistory, createHashHistory } from 'history';

import { dispatch } from '../store';

// Use BrowserHistory in the web browser and HashHistory
// in the mobile apps as we need to keep relative resource
// paths for the mobile which are fundamentally incompatible
// with browser side URL paths routing.
// TODO: Replace this with React Router DOM
// `useHistory` hook after full migration to React.
export const history = window.isCordova ? createHashHistory() : createBrowserHistory();

// TODO: Deprecate in favor of <Link /> and <Redirect />
export function navigateTo({ pathname, search }) {
  // Push the new URL state to browser history only
  // if the new URL differs from the current one.
  const url = `${pathname}${search}`;
  if (url !== `${history.location.pathname}${history.location.search}`) {
    history.push(url);
  }
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

export function useSolarEnabled() {
  return useSearchParams().get('solar') === 'true';
}

export function useWindEnabled() {
  return useSearchParams().get('wind') === 'true';
}

export function useSolarToggledLocation() {
  const location = useLocation();
  const searchParams = useSearchParams();
  const solarEnabled = useSolarEnabled();

  return useMemo(
    () => {
      searchParams.set('solar', !solarEnabled);
      return {
        pathname: location.pathname,
        search: searchParams.toString(),
      };
    },
    [location, searchParams, solarEnabled],
  );
}

export function useWindToggledLocation() {
  const location = useLocation();
  const searchParams = useSearchParams();
  const windEnabled = useWindEnabled();

  return useMemo(
    () => {
      searchParams.set('wind', !windEnabled);
      return {
        pathname: location.pathname,
        search: searchParams.toString(),
      };
    },
    [location, searchParams, windEnabled],
  );
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

//
// Redux state sync
//

// TODO: Remove once we don't need the copy of URL state in the Redux state anymore
// See https://github.com/tmrowco/electricitymap-contrib/issues/2296.
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
