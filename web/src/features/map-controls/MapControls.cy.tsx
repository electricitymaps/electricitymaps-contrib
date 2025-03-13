import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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

  it('can change language', () => {
    cy.viewport(800, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <I18nextProvider i18n={i18n}>
          <MapControls />
        </I18nextProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid=language-selector-open-button]').click();
    cy.contains('English').click();
    cy.contains('country');
    cy.contains('zone');
    cy.contains('production');
    cy.contains('consumption');
    cy.get('[data-testid=language-selector-open-button]').click();
    cy.contains('Deutsch').click();
    cy.contains('Produktion');
    cy.contains('Verbrauch');
    cy.get('[data-testid=language-selector-open-button]').click();
    cy.contains('Svenska').click();
    cy.contains('produktion');
    cy.contains('konsumtion');
    cy.contains('land');
    cy.contains('zon');
    cy.get('[data-testid=language-selector-open-button]').click();
    cy.contains('English').click();
  });

  it('can change theme', () => {
    cy.viewport(800, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <MapControls />
      </QueryClientProvider>
    );
    cy.get('[data-testid=theme-selector-open-button]').click();
    cy.contains('System');
    cy.contains('Light')
      .click({ force: true })
      .should(() => {
        expect(localStorage.getItem('theme')).to.eq('"light"');
      });
    cy.get('[data-testid=theme-selector-open-button]').click();
    cy.contains('Dark')
      .click({ force: true })
      .should(() => {
        expect(localStorage.getItem('theme')).to.eq('"dark"');
      });
  });
});
