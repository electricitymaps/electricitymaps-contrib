export const isRemoteParam = () => {
  return new URLSearchParams(window.location.search).get('remote') === 'true';
};

export const isAggregatedViewFF = () => {
  return new URLSearchParams(window.location.search).get('aggregatedViewFF') === 'true';
};
