describe('Onboarding', () => {
  it('Asserts onboarding works', () => {
    cy.visit('/map');
    cy.get('[data-test-id=onboarding]').should('be.visible');
    cy.get('.modal-footer .modal-footer-circle:nth-child(1)').should('have.class', 'highlight');
    cy.get('.modal-right-button').click();
    cy.get('.modal-footer .modal-footer-circle:nth-child(2)').should('have.class', 'highlight');
    cy.contains('See how much');
    cy.get('.modal-right-button').click();
    cy.get('.modal-right-button').click();
    cy.get('.modal-right-button').should('have.class', 'green');
    cy.get('.modal-right-button')
      .click()
      .should(() => {
        expect(localStorage.getItem('onboardingSeen')).to.eq('true');
      });

    cy.get('[data-test-id=onboarding]').should('not.exist');
    cy.visit('/map');
    cy.get('[data-test-id=onboarding]').should('not.exist');
  });
});
