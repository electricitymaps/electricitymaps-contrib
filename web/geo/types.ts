export interface ZoneConfig {
  [key: string]: {
    subZoneNames?: string[];
    bounding_box: number[];
  };
}
