import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'jotai';
import { useHydrateAtoms } from 'jotai/utils';
import { BrowserRouter } from 'react-router-dom';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';

import Map from './Map';

const zonesToTest = ['DE', 'FR', 'NL', 'NO-NO1', 'SE-SE1', 'CH', 'ES'];

type ZoneLayer = {
  id: string;
  type: string;
  source: string;
  paint: {
    'fill-color': any;
  };
  layout: any;
};

type ZonesSnapshot = {
  [zoneCode: string]: ZoneLayer;
};

const zonesSnapshot: ZonesSnapshot = {
  DE: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  FR: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  NL: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  'NO-NO1': {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  'SE-SE1': {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  CH: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  ES: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
};
const HydrateAtoms = ({ initialValues, children }: any) => {
  useHydrateAtoms(initialValues);
  return children;
};

function TestProvider({ initialValues, children }: any) {
  return (
    <Provider>
      <HydrateAtoms initialValues={initialValues}>{children}</HydrateAtoms>
    </Provider>
  );
}

const handleMapLoad = (map: any) => {
  const features = map.queryRenderedFeatures({ layers: ['zones-clickable-layer'] });
  assert.exists(features);
  assert.isArray(features);
  for (const zoneId of zonesToTest) {
    const zone = features.find((f: any) => f.properties?.zoneId === zoneId)?.layer;
    if (!zone) {
      throw new Error(`Zone with ID ${zoneId} not found.`);
    }
    assert.deepEqual(zone, zonesSnapshot[zoneId]);
  }
};

describe('Map Component', () => {
  it('should display loading state initially', () => {
    const queryClient = new QueryClient();

    cy.intercept('v7/state/hourly', { fixture: 'v7/state/hourly' });
    cy.intercept('v7/state/last_hour', { fixture: 'v7/state/last_hour' });

    cy.mount(
      <TestProvider
        initialValues={[
          [
            selectedDatetimeIndexAtom,
            {
              datetimeString: '2022-12-05T08:00:00Z',
              index: 0,
            },
          ],
        ]}
      >
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Map onMapLoad={handleMapLoad} />
          </BrowserRouter>
        </QueryClientProvider>
      </TestProvider>
    );
    cy.get('[data-test-id=exchange-layer]').should('be.visible');
    cy.get('[data-test-id=wind-layer]').should('exist');
    cy.get('.mapboxgl-map').should('be.visible');
  });
});
