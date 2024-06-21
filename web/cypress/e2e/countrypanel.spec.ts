/* eslint-disable @typescript-eslint/no-unsafe-member-access */
// TODO: Convert to component test
describe('Country Panel', () => {
  beforeEach(() => {
    cy.interceptAPI('v8/state/hourly');
    cy.interceptAPI('v8/state/last_hour');
    cy.interceptAPI('v8/meta');
  });

  it('interacts with details', () => {
    cy.interceptAPI('v8/details/hourly/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess('v8/state/hourly');
    cy.waitForAPISuccess('v8/details/hourly/DK-DK2');
    cy.get('[data-test-id=loading-overlay]').should('not.exist');
    cy.contains('East Denmark');
    cy.contains('Carbon Intensity');
    cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').contains('73');
    // cy.get('[data-test-id=zone-header-lowcarbon-gauge]').trigger('mouseover');
    // cy.contains('Includes renewables and nuclear');
    cy.get('[data-test-id=zone-header-lowcarbon-gauge]').trigger('mouseout');

    cy.contains('Carbon emissions').should('have.attr', 'aria-checked', 'false');
    cy.contains('Carbon emissions').click().should('have.attr', 'aria-checked', 'true');
    cy.contains('0 t');
    cy.contains('Electricity consumption').click();

    // // test graph tooltip
    // cy.get('[data-test-id=details-carbon-graph]').trigger('mousemove', 'left');
    // // ensure hovering the graph does not change underlying data
    // cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').should(
    //   'have.text',
    //   '232'
    // );
    cy.get('[data-test-id=time-slider-input] ').should(
      'have.attr',
      'aria-valuenow',
      '24'
    );
    // ensure tooltip is shown and changes depending on where on the graph is being hovered
    cy.get('[data-test-id=details-carbon-graph]').trigger('mousemove', 'left');
    cy.get('[data-test-id=carbon-chart-tooltip]').should('be.visible');
    cy.get('[data-test-id=carbon-chart-tooltip] ').should('contain.text', '72');

    cy.get('[data-test-id=details-carbon-graph]').trigger('mouseout');
    cy.get('[data-test-id=details-carbon-graph]').trigger('mousemove', 'center');
    cy.get('[data-test-id=carbon-chart-tooltip]').should('contain.text', '64');
    cy.get('[data-test-id=details-carbon-graph]').trigger('mouseout');

    // cy.get('[data-test-id=time-slider-input] ').setSliderValue(1_661_306_400_000);
    cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').should(
      'contain.text',
      '73'
    );

    cy.get('[data-test-id=left-panel-back-button]').click();
  });

  // TODO bring back when we have a no recent data message
  it.skip('asserts countryPanel contains "no-recent-data" message', () => {
    cy.interceptAPI('v8/details/hourly/UA');
    cy.visit('/zone/UA?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.waitForAPISuccess('v8/state/hourly');
    cy.waitForAPISuccess('v8/details/hourly/UA');

    cy.get('[data-test-id=no-data-overlay-message]')
      .should('exist')
      .contains('Data is temporarily unavailable for the selected time');
  });

  it('asserts countryPanel contains no parser message when zone has no data', () => {
    cy.interceptAPI('v8/details/hourly/CN');
    cy.visit('/zone/CN?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.waitForAPISuccess('v8/state/last_hour');
    cy.waitForAPISuccess('v8/state/hourly');
    cy.waitForAPISuccess('v8/details/hourly/CN');
    cy.get('[data-test-id=no-parser-message]').should('exist');
  });
});
