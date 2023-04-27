import { SettingsModalContent } from './SettingsModal';

it('can change language', () => {
  cy.viewport(500, 500);
  cy.mount(<SettingsModalContent />);
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
  cy.mount(<SettingsModalContent />);
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
