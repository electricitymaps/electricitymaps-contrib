describe('History', () => {
  it('Asserts visiting zone requests history data succesfully', () => {
    cy.intercept('https://app-backend.electricitymap.org/v4/history?countryCode=FR').as('fetchHistory');
    cy.visit('/zone/FR?remote=true');
    cy.wait('@fetchHistory').its('response.statusCode').should('eq', 200);
  });
});
