/* eslint-disable no-undef */
describe('Onboarding appears for the first time', () => {
  it('Asserts onboarding appears', () => {
    cy.visit('localhost:8080/map');
    cy.get('[data-test-id=onboarding]').should('exist');
  });
});

describe('Onboarding does not appear', () => {
  it('Asserts onboarding does not appear when already seen', () => {
    window.localStorage.setItem('onboardingSeen', true);
    cy.visit('localhost:8080/map');
    cy.get('[data-test-id=onboarding]').should('not.exist');
  });
});
