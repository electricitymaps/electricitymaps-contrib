/* eslint-disable @typescript-eslint/no-unsafe-member-access */
// TODO: Convert to component test
describe('Country Panel', () => {
  beforeEach(() => {
    cy.interceptAPI('v9/state/hourly');
    cy.interceptAPI('v9/meta');
  });

  it('interacts with details', () => {
    cy.interceptAPI('v9/details/hourly/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly');
    cy.waitForAPISuccess('v9/details/hourly/DK-DK2');
    cy.get('[data-test-id=loading-overlay]').should('not.exist');
    cy.contains('East Denmark');
    cy.contains('Carbon Intensity');
    cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').contains('73');
    // cy.get('[data-test-id=zone-header-lowcarbon-gauge]').trigger('mouseover');
    // cy.contains('Includes renewables and nuclear');
    cy.get('[data-test-id=zone-header-lowcarbon-gauge]').trigger('mouseout');

    cy.get('[data-test-id=toggle-button-emissions]').should(
      'have.attr',
      'aria-checked',
      'false'
    );
    cy.get('[data-test-id=toggle-button-emissions]')
      .click()
      .should('have.attr', 'aria-checked', 'true');
    cy.contains('0 t');
    cy.get('[data-test-id=toggle-button-electricity]').click();

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
    cy.interceptAPI('v9/details/hourly/UA');
    cy.visit('/zone/UA?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.waitForAPISuccess('v9/state/hourly');
    cy.waitForAPISuccess('v9/details/hourly/UA');

    cy.get('[data-test-id=no-data-overlay-message]')
      .should('exist')
      .contains('Data is temporarily unavailable for the selected time');
  });

  it('asserts countryPanel contains no parser message when zone has no data', () => {
    // Add all required API intercepts
    cy.interceptAPI('v9/state/hourly');
    cy.interceptAPI('v9/details/hourly/CN');
    cy.interceptAPI('v9/meta'); // Add this if needed

    cy.visit('/zone/CN/24h?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });

    cy.waitForAPISuccess('v9/state/hourly');
    cy.waitForAPISuccess('v9/details/hourly/CN');

    cy.get('[data-test-id=no-parser-message]').should('exist');
  });

  it('scrolls to anchor element if provided a hash in url', () => {
    cy.interceptAPI('v9/details/hourly/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB#origin_chart', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly');
    cy.waitForAPISuccess('v9/details/hourly/DK-DK2');
    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('#origin_chart').should('be.visible');
  });

  it('scrolls to anchor element if provided a hash with caps in url', () => {
    cy.interceptAPI('v9/details/hourly/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB#oRiGiN_ChArT', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly');
    cy.waitForAPISuccess('v9/details/hourly/DK-DK2');
    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('#origin_chart').should('be.visible');
  });

  it('does not scroll or error if provided a non-sensical hash in url', () => {
    cy.interceptAPI('v9/details/hourly/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB##not-a-thing', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly');
    cy.waitForAPISuccess('v9/details/hourly/DK-DK2');
    cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').should(
      'be.visible'
    );
  });
});
