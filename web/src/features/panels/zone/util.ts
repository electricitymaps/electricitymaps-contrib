import { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';

import zonesConfigJSON from '../../../../config/zones.json'; // Todo: improve how to handle json configs
import { CombinedZonesConfig } from '../../../../geo/types';

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
  AGGREGATE_DISABLED = 'aggregate_disabled',
  FULLY_DISABLED = 'fully_disabled',
  NO_INFORMATION = 'no_information',
  NO_REAL_TIME_DATA = 'dark',
  AVAILABLE = 'available',
  UNKNOWN = 'unknown',
}

export const getZoneDataStatus = (
  zoneId: string,
  zoneDetails: ZoneDetails | undefined,
  timeAverage: TimeAverages
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
    return ZoneDataStatus.NO_INFORMATION;
  }

  if (
    config.zones[zoneId].aggregates_displayed &&
    !config.zones[zoneId].aggregates_displayed.includes(timeAverage)
  ) {
    if (config.zones[zoneId].aggregates_displayed[0] === 'none') {
      return ZoneDataStatus.FULLY_DISABLED;
    }
    return ZoneDataStatus.AGGREGATE_DISABLED;
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

export function showEstimationFeedbackCard(
  collapsedNumber: number,
  isFeedbackCardVisibile: boolean,
  hasFeedbackCardBeenSeen: string | boolean,
  setHasFeedbackCardBeenSeen: (value: boolean) => void
) {
  if ((!hasFeedbackCardBeenSeen && collapsedNumber > 0) || isFeedbackCardVisibile) {
    if (!hasFeedbackCardBeenSeen) {
      setHasFeedbackCardBeenSeen(true);
    }
    return true;
  }
  return false;
}

export const isGenerationOnlyZone = (zoneId: string): boolean =>
  config.zones[zoneId]?.generation_only ?? false;
