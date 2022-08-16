// @ts-expect-error TS(7031): Binding element 'longitude' implicitly has an 'any... Remove this comment to see the full error message
export function getCenteredLocationViewport([longitude, latitude]) {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
    latitude,
    longitude,
    zoom: 4,
  };
}

// If the panel is open the zoom doesn't appear perfectly centered because
// it centers on the whole window and not just the visible map part, which
// is something one could fix in the future.
export function getCenteredZoneViewport(zone: any) {
  return getCenteredLocationViewport(zone.properties.center);
}
