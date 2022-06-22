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

    cy.get('.country-col').contains('182');
    cy.get('input.time-slider-input').should('have.class', 'day');
    cy.get('input.time-slider-input').setSliderValue('1641243600000');
    cy.get('input.time-slider-input').should('have.class', 'night');
    cy.get('.country-col').contains('124');

    cy.get('.left-panel-back-button').click();
  });

  it('asserts countryPanel contains no parser message when zone has no data', () => {
    cy.visit('/zone/CN?remote=true');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
