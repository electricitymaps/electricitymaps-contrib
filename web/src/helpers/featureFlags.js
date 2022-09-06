export const isRemoteParam = () => {
  return new URLSearchParams(window.location.search).get('remote') === 'true';
};

export const aggregatedViewFFEnabled = () => {
  return new URLSearchParams(window.location.search).get('aggregatedViewFF') === 'true';
};
