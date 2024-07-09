/* eslint-disable no-useless-escape */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'jotai';
import { useHydrateAtoms } from 'jotai/utils';
import { BrowserRouter } from 'react-router-dom';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';

import Map from './Map';

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

describe('Map Component', () => {
  it('should display loading state initially', () => {
    const queryClient = new QueryClient();
    cy.intercept('GET', /v8\/state\/hourly\?cacheKey=.*/, {
      fixture: 'v8/state/hourly',
    }).as('getHourlyState');
    cy.intercept('GET', /v8\/state\/last_hour\?cacheKey=.*/, {
      fixture: 'v8/state/last_hour',
    }).as('getLastHourState');
    cy.intercept('GET', 'v8/meta', { fixture: 'v8/meta' });

    cy.mount(
      <TestProvider
        initialValues={[
          [
            selectedDatetimeIndexAtom,
            {
              datetime: new Date('2024-05-01T17:00:00+00:00'),
              index: 0,
            },
          ],
        ]}
      >
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Map />
          </BrowserRouter>
        </QueryClientProvider>
      </TestProvider>
    );
    cy.wait('@getHourlyState');
    cy.wait('@getLastHourState');
    cy.get('[data-test-id=exchange-layer]').should('be.visible');
    cy.get('[data-test-id=wind-layer]').should('exist');
    cy.get('.maplibregl-map').should('be.visible');
    cy.get('.maplibregl-canvas').should('be.visible');
    cy.get('[data-test-id=exchange-arrow-JP-TH-\\>JP-TK]').should('be.visible');
  });
});
