describe('Country Panel', () => {
  it('asserts countryPanel contains carbon intensity when available', () => {
    cy.visit('/zone/SE?remote=true');
    cy.get('[data-test-id=carbon-intensity').should('exist');
  });

  it('asserts countryPanel contains no parser message', () => {
    cy.visit('/zone/CN?remote=true');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
