import { Properties } from '@turf/turf';
import { Feature, MultiPolygon, Polygon } from 'geojson';
import { describe, expect, it, vi } from 'vitest';

import { handleMultiPolygon, handlePolygon, log } from './utilities';

describe('log', () => {
  it('should log the correct error message with formatting', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const message = 'Test error message';
    log(message);

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      '\u001B[31m%s\u001B[0m',
      `ERROR: ${message}`
    );

    consoleErrorSpy.mockRestore();
  });
});

describe('handlePolygon', () => {
  it('should correctly handle a valid polygon feature', () => {
    const feature: Feature<Polygon, Properties> = {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [0, 0],
            [0, 1],
            [1, 1],
            [1, 0],
            [0, 0],
          ],
        ],
      },
      properties: {
        name: 'Test Polygon',
      },
    };

    const actual = handlePolygon(feature);

    expect(actual).toMatchSnapshot();
  });
});

describe('handleMultiPolygon', () => {
  it('should correctly handle a valid MultiPolygon feature', () => {
    const feature: Feature<MultiPolygon, Properties> = {
      type: 'Feature',
      geometry: {
        type: 'MultiPolygon',
        coordinates: [
          [
            [
              [0, 0],
              [0, 1],
              [1, 1],
              [1, 0],
              [0, 0],
            ],
          ],
          [
            [
              [2, 2],
              [2, 3],
              [3, 3],
              [3, 2],
              [2, 2],
            ],
          ],
        ],
      },
      properties: {
        name: 'Test MultiPolygon',
      },
    };

    const actual = handleMultiPolygon(feature);

    expect(actual).toMatchSnapshot();
  });
});
