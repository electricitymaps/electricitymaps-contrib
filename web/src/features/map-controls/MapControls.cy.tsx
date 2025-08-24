import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'jotai';
import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';

import MapControls from './MapControls';

describe('MapControls', () => {
  const queryClient = new QueryClient();

  beforeEach(() => {
    cy.intercept('/feature-flags', {
      body: { 'consumption-only': false },
    });
  });

  it('can toggle settings modal', () => {
    cy.viewport(800, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <Provider>
          <I18nextProvider i18n={i18n}>
            <MapControls />
          </I18nextProvider>
        </Provider>
      </QueryClientProvider>
    );

    cy.get('[data-testid=settings-button]').should('exist');
    cy.get('[data-testid=settings-button]').click();

    // Since the settings modal opens, we can check if the settings content is visible
    cy.contains('theme').should('exist');
  });

  it('can toggle layers modal', () => {
    cy.viewport(800, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <Provider>
          <I18nextProvider i18n={i18n}>
            <MapControls />
          </I18nextProvider>
        </Provider>
      </QueryClientProvider>
    );

    cy.get('[data-testid=layers-button]').should('exist');
    cy.get('[data-testid=layers-button]').click();

    // Check if the layers modal content is visible
    cy.contains(/wind layer|solar layer/i).should('exist');
  });
});
