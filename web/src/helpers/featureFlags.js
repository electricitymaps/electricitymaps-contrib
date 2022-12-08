export const isRemoteParam = () => {
  return new URLSearchParams(window.location.search).get('remote') === 'true';
};
