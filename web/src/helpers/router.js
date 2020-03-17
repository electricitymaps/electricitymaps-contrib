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

  const searchParams = Object.assign({},
    customDate ? { datetime: customDate } : {},
    selectedZoneName ? { countryCode: selectedZoneName } : {},
    showPageState ? { page: showPageState } : {},
    solarEnabled ? { solar: solarEnabled } : {},
    useRemoteEndpoint ? { remote: useRemoteEndpoint } : {},
    windEnabled ? { wind: windEnabled } : {});
  const urlSearch = `?${(new URLSearchParams(searchParams)).toString()}`;

  if (urlSearch !== window.location.search) {
    if (thirdPartyServices._ga) {
      thirdPartyServices._ga.config({ page_path: urlSearch });
    }
    window.history.pushState(searchParams, '', urlSearch);
  }
}
