import { ZoneDetails } from 'types';
import { TimeRange } from 'utils/constants';
import { describe, expect, it } from 'vitest';

import {
  getContributors,
  getDisclaimer,
  getHasSubZones,
  getZoneDataStatus,
  isGenerationOnlyZone,
  showEstimationFeedbackCard,
  ZoneDataStatus,
} from './util';

describe('getContributors', () => {
  it('should return contributors for a zone', () => {
    const result = getContributors('FI');
    expect(result).toMatchSnapshot();
  });
});

describe('getDisclaimer', () => {
  it('should return disclaimer for a zone', () => {
    const result = getDisclaimer('NL');
    expect(result).toMatchSnapshot();
  });
});

describe('getHasSubZones', () => {
  it('should return null when the zoneId is falsy', () => {
    const result = getHasSubZones(undefined);
    expect(result).toEqual(null);
  });

  it('should return false when zone has no subzones', () => {
    const result = getHasSubZones('FI');
    expect(result).toEqual(false);
  });

  it('should return true when zone has subzones', () => {
    const result = getHasSubZones('SE');
    expect(result).toEqual(true);
  });
});

describe('getZoneDataStatus', () => {
  it('should return ZoneDataStatus.UNKNOWN when zoneDetails is falsy', () => {
    const result = getZoneDataStatus(
      'FI',
      undefined as unknown as ZoneDetails,
      TimeRange.H72
    );
    expect(result).toEqual(ZoneDataStatus.UNKNOWN);
  });

  it.todo('should return ZoneDataStatus.AVAILABLE when zoneDetails.hasData is true');

  it.todo(
    'should return ZoneDataStatus.NO_INFORMATION when there is no config for the zone'
  );

  it.todo(
    'should return ZoneDataStatus.FULLY_DISABLED when aggregates_displayed is ["none"]'
  );

  it.todo(
    'should return ZoneDataStatus.AGGREGATE_DISABLED when timeRange is not included in aggregates_displayed'
  );

  it.todo(
    'should return ZoneDataStatus.NO_INFORMATION when there are no production parsers and no defined estimation method in the config'
  );

  it.todo('should return ZoneDataStatus.NO_REAL_TIME_DATA otherwise');
});

describe('isGenerationOnlyZone', () => {
  it('should return true when zone is generation only', () => {
    const result = isGenerationOnlyZone('US-CAR-YAD');
    expect(result).toEqual(true);
  });

  it('should return false when zone is not generation only', () => {
    const result = isGenerationOnlyZone('DK-DK1');
    expect(result).toEqual(false);
  });
});

describe('showEstimationFeedbackCard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return true when feedbackCard is currently not shown, card has not been seen before and it has been collapsed', () => {
    const result = showEstimationFeedbackCard(1, false, false, () => {});
    expect(result).toEqual(true);
  });

  it('should return true when isFeedbackCardVisibile is true', () => {
    const result = showEstimationFeedbackCard(1, true, true, () => {});
    expect(result).toEqual(true);
  });

  it('should return false when conditions are not met', () => {
    const result = showEstimationFeedbackCard(0, false, true, () => {});
    expect(result).toEqual(false);
  });

  it('should return false when conditions are not met', () => {
    const result = showEstimationFeedbackCard(2, false, true, () => {});
    expect(result).toEqual(false);
  });
});
