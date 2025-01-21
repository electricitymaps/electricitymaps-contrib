import { afterEach, describe, expect, it, vi } from 'vitest';

import i18next from './i18n';
import { translateIfExists } from './translation';

describe('translateIfExists', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should return the translation if the key exists', () => {
    vi.spyOn(i18next, 'exists').mockImplementationOnce(() => true);
    vi.spyOn(i18next, 't').mockImplementationOnce(() => 'Austria');

    const translation = translateIfExists('zoneShortName.AT.zoneName');

    expect(translation).to.equal('Austria');
  });

  it('should return an empty string if the key does not exist', () => {});
  vi.spyOn(i18next, 'exists').mockImplementationOnce(() => false);
  vi.spyOn(i18next, 't').mockImplementationOnce(() => 'Austria');

  const translation = translateIfExists('zoneShortName.AT.zoneName');

  expect(translation).to.equal('');
});

// TODO: Mocking these tests is currently not possible or easy due to the translation
// setup. We should in the future investigate how to better mock translations.
describe('getZoneName', () => {
  it.todo('should return the zone name if it exists');
});

describe('getShortenedZoneNameWithCountry', () => {
  it.todo('should return the shortened zone name with country');
});
