import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';

import { LanguageSelector } from './LanguageSelector';

it('mounts', () => {
  cy.mount(
    <I18nextProvider i18n={i18n}>
      <LanguageSelector />
    </I18nextProvider>
  );
  cy.get('[data-test-id=language-selector-open-button]').click();
  cy.contains('English');
  cy.contains('Français');
  cy.contains('Deutsch');
  cy.contains('Español');
  cy.contains('Italiano');
  cy.contains('Nederlands');
  cy.contains('Polski');
  cy.contains('Português');
  cy.contains('Svenska');
  cy.contains('中文');
  cy.contains('日本語');
  cy.contains('한국어');

  cy.get('button').contains('Italiano').click();

  cy.get('[data-test-id=language-selector-open-button]').trigger('mouseover');

  cy.get('.relative').contains('Seleziona la lingua');
});
