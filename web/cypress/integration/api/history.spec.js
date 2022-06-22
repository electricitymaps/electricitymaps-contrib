describe('History', () => {
  it('Asserts visiting zone requests history data succesfully', () => {
    cy.intercept('http://localhost:8001/v5/history/hourly?countryCode=DK-DK2').as('fetchHistory');
    cy.visit('/zone/DK-DK2');
    cy.wait('@fetchHistory').its('response.statusCode').should('eq', 302); // mockserver redirects content
  });
});
