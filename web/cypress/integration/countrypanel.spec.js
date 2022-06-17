describe('Country Panel', () => {
  it('interacts with details', () => {
    cy.visit('/zone/DK-DK2?skip-onboarding=true');
    cy.contains('East Denmark');
    cy.contains('Carbon Intensity');
    cy.get('#country-lowcarbon-gauge').trigger('mousemove');
    cy.contains('Includes renewables and nuclear');
    cy.get('#country-lowcarbon-gauge').trigger('mouseout');
    cy.contains('Carbon emissions').should('not.have.class', 'selected');
    cy.contains('Carbon emissions').click().should('have.class', 'selected');
    cy.contains('0 t/min');
  });

  it('asserts countryPanel contains no parser message', () => {
    cy.visit('/zone/CN');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
