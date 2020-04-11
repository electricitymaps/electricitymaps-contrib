import thirdPartyServices from '../services/thirdparty';

export function updateURLFromState(state) {
  const {
    customDate,
    selectedZoneName,
    showPageState,
    solarEnabled,
    useRemoteEndpoint,
    windEnabled,
  } = state.application;

  // Build search params from application state, ignoring falsey values
  const searchParams = Object.assign({},
    customDate ? { datetime: customDate } : {},
    selectedZoneName ? { countryCode: selectedZoneName } : {},
    showPageState ? { page: showPageState } : {},
    solarEnabled ? { solar: solarEnabled } : {},
    useRemoteEndpoint ? { remote: useRemoteEndpoint } : {},
    windEnabled ? { wind: windEnabled } : {});

  // Build the URL search string from the search params
  const urlSearch = `?${(new URLSearchParams(searchParams)).toString()}`;

  // Push the new URL state to browser history and track
  // it only if the new URL differs from the current one
  if (urlSearch !== window.location.search) {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: urlSearch });
    }
    window.history.pushState(searchParams, '', urlSearch);
  }
}
