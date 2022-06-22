describe('TimeController', () => {
  it('interacts with the timecontroller on map', () => {
    cy.visit('/zone/DE?skip-onboarding=true');

    // Intercepts all API network requests and serves fixtures directly
    cy.interceptAPI('v5/state/hourly');
    cy.interceptAPI('v5/history/hourly?countryCode=DE');
    cy.interceptAPI('v5/state/daily');
    cy.interceptAPI('v5/state/monthly');
    cy.interceptAPI('v5/state/yearly');
    cy.interceptAPI('v5/history/daily?countryCode=DE');
    cy.interceptAPI('v5/history/monthly?countryCode=DE');
    cy.interceptAPI('v5/history/yearly?countryCode=DE');

    // Hourly
    cy.waitForAPISuccess(`v5/state/hourly`);
    cy.waitForAPISuccess(`v5/history/hourly?countryCode=DE`);
    cy.contains('LIVE');
    cy.get('[data-test-id=co2-square-value').should('have.text', '451');
    cy.get('[data-test-id=date-display').should('have.text', '22 June 2022 at 07:00');
    cy.get('input.time-slider-input-new').setSliderValue('1655834400000');
    cy.get('[data-test-id=date-display').should('have.text', '21 June 2022 at 20:00');
    cy.get('[data-test-id=co2-square-value').should('have.text', '461');

    // Monthly
    cy.get('[data-test-id="time-controls-daily-btn"]').click();
    cy.waitForAPISuccess(`v5/state/daily`);
    cy.waitForAPISuccess(`v5/history/daily?countryCode=DE`);
    cy.get('[data-test-id=co2-square-value').should('have.text', '385');
    cy.get('[data-test-id=date-display').should('have.text', '21 June 2022');
    cy.get('input.time-slider-input-new').setSliderValue('1653782400000');
    cy.get('[data-test-id=date-display').should('have.text', '29 May 2022');
    cy.get('[data-test-id=co2-square-value').should('have.text', '316');

    // Yearly
    cy.get('[data-test-id="time-controls-monthly-btn"]').click();
    cy.waitForAPISuccess(`v5/state/monthly`);
    cy.waitForAPISuccess(`v5/history/monthly?countryCode=DE`);
    cy.get('[data-test-id=co2-square-value').should('have.text', '328');
    cy.get('[data-test-id=date-display').should('have.text', 'May 2022');
    cy.get('input.time-slider-input-new').setSliderValue('1640995200000');
    cy.get('[data-test-id=date-display').should('have.text', 'January 2022');
    cy.get('[data-test-id=co2-square-value').should('have.text', '360');

    // 5 Years
    cy.get('[data-test-id="time-controls-yearly-btn"]').click();
    cy.waitForAPISuccess(`v5/state/yearly`);
    cy.waitForAPISuccess(`v5/history/yearly?countryCode=DE`);
    cy.get('[data-test-id=co2-square-value').should('have.text', '331');
    cy.get('[data-test-id=date-display').should('have.text', '2021');
    cy.get('input.time-slider-input-new').setSliderValue('1577836800000');
    cy.get('[data-test-id=date-display').should('have.text', '2020');
    cy.get('[data-test-id=co2-square-value').should('have.text', '295');
  });
});
