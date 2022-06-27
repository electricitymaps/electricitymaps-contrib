describe('Country Panel', () => {
  it('interacts with details', () => {
    cy.visit('/zone/DK-DK2?skip-onboarding=true');
    cy.contains('East Denmark');
    cy.contains('Carbon Intensity');
    cy.get('.left-panel-zone-details .country-col').contains('152');
    cy.get('#country-lowcarbon-gauge').trigger('mousemove');
    cy.contains('Includes renewables and nuclear');
    cy.get('#country-lowcarbon-gauge').trigger('mouseout');

    cy.contains('Carbon emissions').should('not.have.class', 'selected');
    cy.contains('Carbon emissions').click().should('have.class', 'selected');
    cy.contains('0 t/min');
    cy.contains('Electricity consumption').click();

    // test graph tooltip
    cy.get('[data-test-id=history-carbon-graph]').trigger('mousemove', 'left');
    // ensure hovering the graph does not change underlying data
    cy.get('.left-panel-zone-details .country-col').contains('152');
    cy.get('input.time-slider-input-new').should('have.value', '1655874000000');
    // ensure tooltip is shown and changes depending on where on the graph is being hovered
    cy.get('#country-tooltip').should('be.visible');
    cy.get('#country-tooltip .country-col').contains('86');
    cy.get('[data-test-id=history-carbon-graph]').trigger('mouseout');
    cy.get('[data-test-id=history-carbon-graph]').trigger('mousemove', 'center');
    cy.get('#country-tooltip .country-col').contains('122');
    cy.get('[data-test-id=history-carbon-graph]').trigger('mouseout');

    cy.get('input.time-slider-input-new').setSliderValue('1655823600000');
    cy.get('.country-col').contains('84');

    cy.get('.left-panel-back-button').click();
  });

  it('asserts countryPanel contains "no-recent-data" message', () => {
    cy.visit('/zone/UA');
    cy.get('.no-data-overlay-message')
      .should('exist')
      .contains('Data is temporarily unavailable for the selected time');
  });

  it('asserts countryPanel contains no parser message when zone has no data', () => {
    cy.visit('/zone/CN?remote=true');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
