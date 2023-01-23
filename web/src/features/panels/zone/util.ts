import { ZoneDetails } from 'types';
import zonesConfigJSON from '../../../../config/zones.json'; // Todo: improve how to handle json configs

type zoneConfigItem = {
  contributors?: string[];
  capacity?: any;
  disclaimer?: string;
  timezone?: string | null;
  bounding_box?: any;
  parsers?: any;
  flag_file_name?: string;
  estimation_method?: string;
};

export enum ZoneDataStatus {
  NO_INFORMATION = 'no_information',
  NO_REAL_TIME_DATA = 'dark',
  AVAILABLE = 'available',
  UNKNOWN = 'unknown',
}

const zonesConfig: Record<string, zoneConfigItem | undefined> = zonesConfigJSON;
export const getZoneDataStatus = (
  zoneId: string,
  zoneDetails: ZoneDetails | undefined
) => {
  // Temporary overwrite for IN-NO
  if (zoneId === 'IN-NO') {
    return ZoneDataStatus.NO_INFORMATION;
  }

  // If there is no zoneDetails, we do not make any assumptions and return unknown
  if (!zoneDetails) {
    return ZoneDataStatus.UNKNOWN;
  }

  // If API returns hasData, we return available regardless
  if (zoneDetails.hasData) {
    return ZoneDataStatus.AVAILABLE;
  }

  // If there is no config for the zone, we assume we do not have any data
  const config = zonesConfig[zoneId];
  if (!config) {
    console.log(config);

    return ZoneDataStatus.NO_INFORMATION;
  }

  // If there are no production parsers or no defined estimation method in the config,
  // we assume we do not have data for the zone
  if (
    config.parsers?.production === undefined &&
    config.estimation_method === undefined
  ) {
    return ZoneDataStatus.NO_INFORMATION;
  }

  // Otherwise, we assume we have data but it is currently missing
  return ZoneDataStatus.NO_REAL_TIME_DATA;
};

export function getContributors(zoneId: string) {
  const config = zonesConfig[zoneId];
  return config?.contributors;
}

export function getDisclaimer(zoneId: string) {
  const config = zonesConfig[zoneId];
  return config?.disclaimer;
}
