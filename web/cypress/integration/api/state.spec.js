describe('State', () => {
  it('Asserts visiting map requests state data correctly', () => {
    cy.visit('/map');
    cy.intercept('http://localhost:8001/v5/state/hourly').as('getState');
    cy.wait('@getState')
      .its('response.statusCode')
      .should('match', /200|304/);
  });
});
