export function updateApplication(key, value) {
  return {
    key,
    value,
    type: 'APPLICATION_STATE_UPDATE',
  };
}
