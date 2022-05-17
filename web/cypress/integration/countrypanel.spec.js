/* eslint-disable no-undef */
describe('countryPanel displays data', () => {
  it('asserts countryPanel contains carbon intensity when available', () => {
    cy.visit('localhost:8080/zone/SE?remote=true');
    cy.get('[data-test-id=carbon-intensity').should('exist');
  });
});

describe('countryPanel does not display data', () => {
  it('asserts countryPanel contains no parser message', () => {
    cy.visit('localhost:8080/zone/CN?remote=true');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
