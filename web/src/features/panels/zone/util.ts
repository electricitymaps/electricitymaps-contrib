import { ZoneDetails } from 'types';
import { TimeRange } from 'utils/constants';

import zonesConfigJSON from '../../../../config/zones.json'; // Todo: improve how to handle json configs
import { CombinedZonesConfig } from '../../../../geo/types';

const { zones, contributors } = zonesConfigJSON as unknown as CombinedZonesConfig;

export const zoneExists = (zoneId: string) => Boolean(zones[zoneId]);

/**
 * A helper function to check if a zone has any subZones
 * Previously this used the following code,
 * but it has since been optimized for size and speed:
 * ```
 * export const getHasSubZones = (zoneId?: string) => {
 *  if (!zoneId) {
 *    return null;
 *  }
 *  const zoneConfig = zones[zoneId];
 *  if (!zoneConfig || !zoneConfig.subZoneNames) {
 *    return false;
 *  }
 *  return zoneConfig.subZoneNames.length > 0;
 *};
 *```
 */
export const getHasSubZones = (zoneId?: string): boolean | null =>
  zoneId ? Boolean(zones[zoneId]?.subZoneNames?.length) : null;

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
  timeRange: TimeRange
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
  const zoneConfig = zones[zoneId];
  if (!zoneConfig) {
    return ZoneDataStatus.NO_INFORMATION;
  }

  if (
    zones[zoneId].aggregates_displayed &&
    !zones[zoneId].aggregates_displayed.includes(timeRange)
  ) {
    if (zones[zoneId].aggregates_displayed[0] === 'none') {
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

export const getContributors = (zoneId: string) =>
  zones[zoneId]?.contributors?.map((index) => contributors[index]) ?? [];

export const getDisclaimer = (zoneId: string) => zones[zoneId]?.disclaimer;

export const showEstimationFeedbackCard = (
  collapsedNumber: number,
  isFeedbackCardVisibile: boolean,
  hasFeedbackCardBeenSeen: string | boolean,
  setHasFeedbackCardBeenSeen: (value: boolean) => void
) => {
  if ((!hasFeedbackCardBeenSeen && collapsedNumber > 0) || isFeedbackCardVisibile) {
    if (!hasFeedbackCardBeenSeen) {
      setHasFeedbackCardBeenSeen(true);
    }
    return true;
  }
  return false;
};

export const isGenerationOnlyZone = (zoneId: string): boolean =>
  zones[zoneId]?.generation_only ?? false;
