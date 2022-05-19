describe('State', () => {
  it('Asserts visiting map requests state data correctly', () => {
    cy.visit('/map?remote=true');
    cy.intercept('https://app-backend.electricitymap.org/v4/state').as('getState');
    cy.wait('@getState').its('response.statusCode').should('eq', 200);
  });
});
