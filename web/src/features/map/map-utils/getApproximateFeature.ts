import { MapGeometry, MapGeometries } from 'types';

// if no feature matches, it means that the selected zone is not in current spatial resolution.
// We cannot include geometries in dependencies, as we don't want to flyTo when user switches
// between spatial resolutions. Therefore we use the following workaround to center on a child
// zone instead.

const checkForUS = (zoneId: string, feature: MapGeometry) => {
  if (zoneId.includes('-')) {
    // We are in country view and want to show a single zone,
    // so we center on the aggregated US zone
    return feature.properties.zoneId === 'US';
  }

  if (zoneId === 'US') {
    // We are in zone view and want to show the aggregated US zone,
    // so we center on US-CENT-SWPP to get in the middle of the US as it by
    // default centers on Alaska otherwise.
    return feature.properties.zoneId === 'US-CENT-SWPP';
  }
};
/**
 * This function takes the zoneId and geometries and returns the first feature that matches the
 * zoneId's country. If no feature matches, it means that the selected zone is not in current
 */
export function getApproximateFeature(zoneId: string, geometries: MapGeometries) {
  const country = zoneId.split('-')[0];
  const child = geometries.features.find((feature) => {
    // Special case for US as it is so large
    if (zoneId.startsWith('US')) {
      return checkForUS(zoneId, feature);
    }
    // Else we just center on the first zone where the country matches
    return feature.properties.countryKey === country;
  });

  return child;
}
