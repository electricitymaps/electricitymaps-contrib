import { isEmpty } from 'lodash';

import thirdPartyServices from '../services/thirdparty';

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

  // Construct search string from the search params
  const search = isEmpty(searchParams) ? '' : `?${(new URLSearchParams(searchParams)).toString()}`;

  // Construct pathname from application state
  let pathname = `/${currentPage}`;
  if (selectedZoneName) {
    pathname += `/${selectedZoneName}`;
  }

  // Build the final URL from all the parts
  const url = `${window.location.origin}${pathname}${search}`;

  // Push the new URL state to browser history and track
  // it only if the new URL differs from the current one
  if (url !== window.location.href) {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: url });
    }
    window.history.pushState({ pathname, search }, '', url);
  }
}
