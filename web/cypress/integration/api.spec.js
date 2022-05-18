describe('API', () => {
  it('Returns 200 for v4/state', () => {
    cy.visit('/map?remote=true');
    cy.intercept({
      method: 'GET',
      url: 'v4/state',
    }).as('getState');

    cy.wait('@getState').its('response.statusCode').should('eq', 200);
  });
});
