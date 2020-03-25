import { isEmpty } from 'lodash';

import thirdPartyServices from '../services/thirdparty';

export function updateURLFromState(history, state) {
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
