describe('State', () => {
  it('Asserts visiting map requests state data correctly', () => {
    cy.visit('/map');
    cy.intercept('http://localhost:8001/v4/state').as('getState');
    cy.wait('@getState').its('response.statusCode').should('eq', 200);
  });
});
