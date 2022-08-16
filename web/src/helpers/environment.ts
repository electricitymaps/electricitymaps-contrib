export function isProduction() {
  return window.location.href.includes('electricitymap');
}

export function isLocalhost() {
  return !isProduction() && !window.location.href.includes('192.');
}

export function isNewClientVersion(version: any) {
  // @ts-expect-error TS(2552): Cannot find name 'VERSION'. Did you mean 'version'... Remove this comment to see the full error message
  return version !== VERSION;
}
