// TODO: Convert to component test and uncomment tests
describe('Onboarding', () => {
  it('Asserts onboarding works', () => {
    cy.visit('/map?lang=en-GB');
    cy.get('[data-test-id=onboarding]').should('be.visible');
  });
});
