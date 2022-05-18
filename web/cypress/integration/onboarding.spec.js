describe('Onboarding', () => {
  it('Asserts onboarding appears', () => {
    cy.visit('/map');
    cy.get('[data-test-id=onboarding]').should('exist');
  });

  it('Asserts onboarding does not appear when already seen', () => {
    // local storage should have been set
    cy.visit('/map');
    cy.get('[data-test-id=onboarding]').should('not.exist');
  });
});
