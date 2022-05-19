describe('Country Panel', () => {
  it('asserts countryPanel contains no parser message', () => {
    cy.visit('/zone/CN?remote=true');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
