/* eslint-disable import/no-extraneous-dependencies -- 'vitest' should be listed in the project's dependencies, not devDependencies */
import { describe, expect, it } from 'vitest';

import { getConfig } from './generateZonesConfig';

describe('generateZonesConfig', () => {
  it('should handle contributors for aggregated countries', () => {
    // TODO: This test is somewhat flaky as it depends on current state of config files.
    // Ideally this should be mocked instead!
    const contributorName = 'tmslaine';

    const result = getConfig();
    const indexOfContributor = result.contributors.indexOf(contributorName);

    // Person should be in the list of contributors
    expect(result.contributors).toContain(contributorName);
    // Person should be in the list of contributors for the zone
    expect(result.zones['DK-DK2'].contributors).toContain(indexOfContributor);
    // Person should be in the list of contributors for the aggregated country
    expect(result.zones['DK'].contributors).toContain(indexOfContributor);
  });
});
