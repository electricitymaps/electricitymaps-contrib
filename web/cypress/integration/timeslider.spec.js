describe('TimeController', () => {
  it('interacts with the timecontroller on map', () => {
    cy.visit('/zone/DK-DK2?skip-onboarding=true');

    // Intercepts all API network requests and serves fixtures directly
    cy.interceptAPI('v5/state/hourly');
    cy.interceptAPI('v5/history/hourly?countryCode=DK-DK2');
    cy.interceptAPI('v5/state/daily');
    cy.interceptAPI('v5/state/monthly');
    cy.interceptAPI('v5/state/yearly');
    cy.interceptAPI('v5/history/daily?countryCode=DK-DK2');
    cy.interceptAPI('v5/history/monthly?countryCode=DK-DK2');
    cy.interceptAPI('v5/history/yearly?countryCode=DK-DK2');

    // Hourly
    cy.waitForAPISuccess(`v5/state/hourly`);
    cy.waitForAPISuccess(`v5/history/hourly?countryCode=DK-DK2`);
    cy.contains('LIVE');
    cy.get('[data-test-id=co2-square-value').should('have.text', '152');
    cy.get('[data-test-id=date-display').should('have.text', '22 June 2022 at 07:00');
    cy.get('input.time-slider-input-new').setSliderValue('1655834400000');
    cy.get('[data-test-id=date-display').should('have.text', '21 June 2022 at 20:00');
    cy.get('[data-test-id=co2-square-value').should('have.text', '108');

    // Monthly
    cy.get('[data-test-id="time-controls-daily-btn"]').click();
    cy.waitForAPISuccess(`v5/state/daily`);
    cy.waitForAPISuccess(`v5/history/daily?countryCode=DK-DK2`);
    cy.get('[data-test-id=co2-square-value').should('have.text', '385');
    cy.get('[data-test-id=date-display').should('have.text', '21 June 2022');
    cy.get('input.time-slider-input-new').setSliderValue('1653782400000');
    cy.get('[data-test-id=date-display').should('have.text', '29 May 2022');
    cy.get('[data-test-id=co2-square-value').should('have.text', '316');

    // Yearly
    cy.get('[data-test-id="time-controls-monthly-btn"]').click();
    cy.waitForAPISuccess(`v5/state/monthly`);
    cy.waitForAPISuccess(`v5/history/monthly?countryCode=DK-DK2`);
    cy.get('[data-test-id=co2-square-value').should('have.text', '328');
    cy.get('[data-test-id=date-display').should('have.text', 'May 2022');
    cy.get('input.time-slider-input-new').setSliderValue('1640995200000');
    cy.get('[data-test-id=date-display').should('have.text', 'January 2022');
    cy.get('[data-test-id=co2-square-value').should('have.text', '360');

    // 5 Years
    cy.get('[data-test-id="time-controls-yearly-btn"]').click();
    cy.waitForAPISuccess(`v5/state/yearly`);
    cy.waitForAPISuccess(`v5/history/yearly?countryCode=DK-DK2`);
    cy.get('[data-test-id=co2-square-value').should('have.text', '331');
    cy.get('[data-test-id=date-display').should('have.text', '2021');
    cy.get('input.time-slider-input-new').setSliderValue('1577836800000');
    cy.get('[data-test-id=date-display').should('have.text', '2020');
    cy.get('[data-test-id=co2-square-value').should('have.text', '295');
  });

  // TODO: Figure out how to get open/drag bottom sheet in Cypress on mobile
  // I have tried a bunch of combinations with mousemove, etc. without success
  it.skip('interacts with the timecontroller on mobile', () => {
    cy.visitOnMobile('/?skip-onboarding=true');
  });
});
