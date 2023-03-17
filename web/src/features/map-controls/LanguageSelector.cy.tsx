import { LanguageSelector } from './LanguageSelector';

it('mounts', () => {
  cy.intercept('/locales/it.json').as('it');
  cy.mount(<LanguageSelector />);
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
  cy.wait('@it').its('request.url').should('include', '/locales/it.json');
});
