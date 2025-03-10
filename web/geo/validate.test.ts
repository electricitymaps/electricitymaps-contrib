import { describe, expect, it } from 'vitest';

import { GEO_CONFIG } from './generateWorld';
import { WorldFeatureCollection } from './types';
import { zeroOverlaps } from './validate';

const mockFeatureCollection: WorldFeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        zoneName: 'SE-SE4',
        countryKey: 'SE',
        isAggregatedView: false,
        isHighestGranularity: true,
      },
      geometry: {
        type: 'MultiPolygon',
        coordinates: [
          [
            [
              [12.301, 57.0397],
              [16.6918, 57.5131],
              [16.4648, 57.1777],
              [16.5836, 57.0446],
              [16.094, 56.4192],
              [16.04, 56.2546],
              [15.8528, 56.0858],
              [15.572, 56.206],
              [15.32, 56.1401],
              [14.6863, 56.1473],
              [14.7691, 56.0314],
              [14.4775, 56.0314],
              [14.2075, 55.821],
              [14.3623, 55.5233],
              [14.1823, 55.3902],
              [13.8835, 55.4332],
              [13.2787, 55.3459],
              [12.9511, 55.4246],
              [12.9295, 55.5792],
              [13.0627, 55.675],
              [12.9223, 55.7495],
              [12.5047, 56.2747],
              [12.7963, 56.2274],
              [12.6199, 56.4192],
              [12.8899, 56.455],
              [12.8719, 56.6496],
              [12.7315, 56.6467],
              [12.5983, 56.8213],
              [12.3751, 56.9115],
              [12.301, 57.0397],
            ],
          ],
          [
            [
              [16.5735, 56.8198],
              [16.8377, 57.0067],
              [17.0334, 57.3303],
              [17.1997, 57.3778],
              [16.3778, 56.2152],
              [16.3778, 56.4701],
              [16.5735, 56.8198],
            ],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: {
        zoneName: 'SE-SE3',
        countryKey: 'SE',
        isAggregatedView: false,
        isHighestGranularity: true,
      },
      geometry: {
        type: 'MultiPolygon',
        coordinates: [
          [
            [
              [17.1681, 61.0533],
              [17.1668, 60.9915],
              [17.3108, 60.7454],
              [17.192, 60.7024],
              [17.5736, 60.648],
              [17.6384, 60.515],
              [17.9192, 60.6008],
              [17.966, 60.5121],
              [18.5636, 60.2273],
              [18.3296, 60.286],
              [18.506, 60.1558],
              [18.8192, 60.1143],
              [18.9488, 59.8996],
              [18.7904, 59.7794],
              [19.0424, 59.7851],
              [18.4124, 59.4917],
              [18.0092, 59.4087],
              [18.2756, 59.3128],
              [18.416, 59.1397],
              [18.0416, 59.0595],
              [17.9012, 58.915],
              [17.75, 58.9236],
              [17.7572, 59.1254],
              [17.6096, 59.0939],
              [17.5916, 58.8678],
              [16.9256, 58.6259],
              [16.2344, 58.6689],
              [16.4108, 58.5973],
              [16.7888, 58.6073],
              [16.94, 58.4914],
              [16.7204, 58.437],
              [16.778, 58.1308],
              [16.6918, 57.5131],
              [12.3011, 57.0394],
              [12.1018, 57.5076],
              [11.9533, 57.367],
              [11.7055, 57.7215],
              [11.6875, 57.8374],
              [11.5541, 57.9587],
              [11.4856, 58.0623],
              [11.3584, 58.145],
              [11.4139, 58.4313],
              [11.2303, 58.3397],
              [11.2879, 58.5801],
              [11.1187, 58.9694],
              [11.3563, 59.091],
              [11.4535, 58.8964],
              [11.6659, 58.9207],
              [11.7847, 59.2184],
              [11.8063, 59.2942],
              [11.6767, 59.559],
              [11.9035, 59.7694],
              [11.8495, 59.8724],
              [12.1447, 59.8982],
              [12.4471, 60.0513],
              [12.5767, 60.3761],
              [12.6091, 60.4863],
              [12.3355, 60.8284],
              [12.3139, 60.9013],
              [12.2815, 61.0158],
              [12.6811, 61.0402],
              [12.8395, 61.2276],
              [12.8539, 61.2548],
              [12.8863, 61.3622],
              [12.5515, 61.5668],
              [12.1771, 61.7113],
              [12.2492, 62.0069],
              [15.8753, 61.1685],
              [17.1681, 61.0533],
            ],
          ],
          [
            [
              [18.0754, 57.567],
              [18.7392, 57.9448],
              [19.3735, 58.0308],
              [18.8425, 57.654],
              [18.8277, 57.2971],
              [18.4737, 56.993],
              [18.1492, 56.9206],
              [18.1196, 57.2253],
              [18.0754, 57.567],
            ],
          ],
        ],
      },
    },
  ],
};
describe('zeroOverlaps', () => {
  it('should not throw if there are no overlaps', () => {
    // assert that function does not throw error
    expect(() => zeroOverlaps(mockFeatureCollection, GEO_CONFIG)).not.toThrow();
  });

  it('should throw on overlaps', () => {
    // Casting to any to be able to modify the coordinates directly
    // as we know this will always be a MultiPolygon
    const overlappingFeatureCollection = { ...mockFeatureCollection } as any;
    overlappingFeatureCollection.features[1].geometry.coordinates[1][0][0][0] = 11.0754;
    overlappingFeatureCollection.features[1].geometry.coordinates[1][0][8][0] = 11.0754;
    // assert that function throws error with specific message
    expect(() => zeroOverlaps(overlappingFeatureCollection, GEO_CONFIG)).toThrow(
      'SE-SE3 overlaps with SE-SE4'
    );
  });
});
