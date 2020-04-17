
export function isProduction() {
  return window.location.href.includes('electricitymap');
}

export function isLocalhost() {
  return !isProduction() && !window.location.href.includes('192.');
}
