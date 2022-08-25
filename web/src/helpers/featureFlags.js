export const isRemoteParam = () => {
  return new URLSearchParams(window.location.search).get('remote') === 'true';
};

export const isAggregatedViewEnabled = () => {
  return new URLSearchParams(window.location.search).get('aggregatedView') === 'true';
};
