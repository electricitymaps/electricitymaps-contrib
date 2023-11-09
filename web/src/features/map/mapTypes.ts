export type FeatureId = string | number | undefined;

export interface HoveredZone {
  featureId: FeatureId;
  zoneId: string;
}

export type MapStyle = {
  ocean: {
    'background-color': string;
  };
  zonesBorder: mapboxgl.LinePaint;
  zonesClickable: mapboxgl.FillPaint;
  zonesHover: mapboxgl.FillPaint;
  statesBorder: mapboxgl.LinePaint;
};
