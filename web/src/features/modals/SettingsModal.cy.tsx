import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';

import i18n from '../../translation/i18n';
import { SettingsModalContent } from './SettingsModal';

describe('SettingsModalContent', () => {
  const queryClient = new QueryClient();

  it('can change language', () => {
    cy.viewport(500, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <I18nextProvider i18n={i18n}>
          <SettingsModalContent />
        </I18nextProvider>
      </QueryClientProvider>
    );
    cy.contains('Wind data is currently unavailable');
    cy.contains('Solar data is currently unavailable');
    cy.get('[data-test-id=language-selector-open-button]').click();
    cy.contains('English').click();
    cy.contains('country');
    cy.contains('zone');
    cy.contains('production');
    cy.contains('consumption');
    cy.get('[data-test-id=language-selector-open-button]').click();
    cy.contains('Deutsch').click();
    cy.contains('Produktion');
    cy.contains('Verbrauch');
    cy.get('[data-test-id=language-selector-open-button]').click();
    cy.contains('Svenska').click();
    cy.contains('produktion');
    cy.contains('konsumtion');
    cy.contains('land');
    cy.contains('zon');
    cy.get('[data-test-id=language-selector-open-button]').click();
    cy.contains('English').click();
  });

  it('can change theme', () => {
    cy.viewport(500, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <I18nextProvider i18n={i18n}>
          <SettingsModalContent />
        </I18nextProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id=theme-selector-open-button]').click();
    cy.contains('System');
    cy.contains('Light')
      .click()
      .should(() => {
        expect(localStorage.getItem('theme')).to.eq('"light"');
      });
    cy.get('[data-test-id=theme-selector-open-button]').click();
    cy.contains('Dark')
      .click()
      .should(() => {
        expect(localStorage.getItem('theme')).to.eq('"dark"');
      });
  });
});
