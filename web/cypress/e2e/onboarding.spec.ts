// TODO: Convert to component test
describe('Onboarding', () => {
  it('Asserts onboarding works', () => {
    // Onboarding is temporarily disabled
    const isDisabled = new Date() < new Date('2022-08-18');
    if (isDisabled) {
      return;
    }

    cy.visit('/map?lang=en-GB');
    cy.get('[data-test-id=onboarding]').should('be.visible');
    cy.get('[data-test-id=onboarding] .modal-footer .modal-footer-circle:nth-child(1)').should(
      'have.class',
      'highlight'
    );
    cy.get('[data-test-id=onboarding] .modal-right-button').click();
    cy.get('[data-test-id=onboarding] .modal-footer .modal-footer-circle:nth-child(2)').should(
      'have.class',
      'highlight'
    );
    cy.contains('See how much');
    cy.get('[data-test-id=onboarding] .modal-right-button').click();
    cy.get('[data-test-id=onboarding] .modal-right-button').click();
    cy.get('[data-test-id=onboarding] .modal-right-button').should('have.class', 'green');
    cy.get('[data-test-id=onboarding] .modal-right-button')
      .click()
      .should(() => {
        /* eslint-disable */
        // @ts-ignore
        expect(localStorage.getItem('onboardingSeen')).to.eq('true');
        /* eslint-enable */
      });

    cy.get('[data-test-id=onboarding]').should('not.exist');
    cy.visit('/map?lang=en-GB');
    cy.get('[data-test-id=onboarding]').should('not.exist');
  });
});
