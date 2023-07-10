import { ZoneDetails } from 'types';
import zonesConfigJSON from '../../../../config/zones.json'; // Todo: improve how to handle json configs
import { CombinedZonesConfig } from '../../../../geo/types';

type zoneConfigItem = {
  contributors?: string[];
  capacity?: any;
  disclaimer?: string;
  timezone?: string | null;
  bounding_box?: any;
  parsers?: any;
  estimation_method?: string;
  subZoneNames?: string[];
};

const config = zonesConfigJSON as unknown as CombinedZonesConfig;

export const getHasSubZones = (zoneId?: string) => {
  if (!zoneId) {
    return null;
  }

  const zoneConfig = config.zones[zoneId];
  if (!zoneConfig || !zoneConfig.subZoneNames) {
    return false;
  }
  return zoneConfig.subZoneNames.length > 0;
};

export enum ZoneDataStatus {
  NO_INFORMATION = 'no_information',
  NO_REAL_TIME_DATA = 'dark',
  AVAILABLE = 'available',
  UNKNOWN = 'unknown',
}

export const getZoneDataStatus = (
  zoneId: string,
  zoneDetails: ZoneDetails | undefined
) => {
  // If there is no zoneDetails, we do not make any assumptions and return unknown
  if (!zoneDetails) {
    return ZoneDataStatus.UNKNOWN;
  }

  // If API returns hasData, we return available regardless
  if (zoneDetails.hasData) {
    return ZoneDataStatus.AVAILABLE;
  }

  // If there is no config for the zone, we assume we do not have any data
  const zoneConfig = config.zones[zoneId];
  if (!zoneConfig) {
    console.log(zoneConfig);

    return ZoneDataStatus.NO_INFORMATION;
  }

  // If there are no production parsers or no defined estimation method in the config,
  // we assume we do not have data for the zone
  if (zoneConfig.parsers === false && zoneConfig.estimation_method === undefined) {
    return ZoneDataStatus.NO_INFORMATION;
  }

  // Otherwise, we assume we have data but it is currently missing
  return ZoneDataStatus.NO_REAL_TIME_DATA;
};

export function getContributors(zoneId: string) {
  return {
    zoneContributorsIndexArray: config.zones[zoneId]?.contributors as number[],
    contributors: config.contributors,
  };
}

export function getDisclaimer(zoneId: string) {
  const zoneConfig = config.zones[zoneId];
  return zoneConfig?.disclaimer;
}
