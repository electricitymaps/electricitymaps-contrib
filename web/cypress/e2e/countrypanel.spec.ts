/* eslint-disable @typescript-eslint/no-unsafe-member-access */
// TODO: Convert to component test
describe('Country Panel', () => {
  beforeEach(() => {
    cy.interceptAPI('v9/state/hourly_72');
    cy.interceptAPI('v9/meta');
  });

  it('interacts with details', () => {
    cy.interceptAPI('v9/details/hourly_72/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-testid=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly_72');
    cy.waitForAPISuccess('v9/details/hourly_72/DK-DK2');
    cy.get('[data-testid=loading-overlay]').should('not.exist');
    cy.contains('East Denmark');
    cy.contains('Carbon Intensity');
    cy.get('[data-testid=left-panel] [data-testid=co2-square-value]').contains('111');
    // cy.get('[data-testid=zone-header-lowcarbon-gauge]').trigger('mouseover');
    // cy.contains('Includes renewables and nuclear');
    cy.get('[data-testid=zone-header-lowcarbon-gauge]').trigger('mouseout');

    cy.get('[data-testid=toggle-button-emissions]').should(
      'have.attr',
      'aria-checked',
      'false'
    );
    cy.get('[data-testid=toggle-button-emissions]')
      .click()
      .should('have.attr', 'aria-checked', 'true');
    cy.contains('0 t');
    cy.get('[data-testid=toggle-button-electricity]').click();

    // // test graph tooltip
    // cy.get('[data-testid=details-carbon-graph]').trigger('mousemove', 'left');
    // // ensure hovering the graph does not change underlying data
    // cy.get('[data-testid=left-panel] [data-testid=co2-square-value]').should(
    //   'have.text',
    //   '232'
    // );
    cy.get('[data-testid=time-slider-input] ').should('have.attr', 'aria-valuenow', '71');
    // ensure tooltip is shown and changes depending on where on the graph is being hovered
    cy.get('[data-testid=details-carbon-graph]').trigger('mousemove', 'left');
    cy.get('[data-testid=carbon-chart-tooltip]').should('be.visible');
    cy.get('[data-testid=carbon-chart-tooltip] ').should('contain.text', '144');

    cy.get('[data-testid=details-carbon-graph]').trigger('mouseout');
    cy.get('[data-testid=details-carbon-graph]').trigger('mousemove', 'center');
    cy.get('[data-testid=carbon-chart-tooltip]').should('contain.text', '57');
    cy.get('[data-testid=details-carbon-graph]').trigger('mouseout');

    // cy.get('[data-testid=time-slider-input] ').setSliderValue(1_661_306_400_000);
    cy.get('[data-testid=left-panel] [data-testid=co2-square-value]').should(
      'contain.text',
      '111'
    );

    cy.get('[data-testid=left-panel-back-button]').click();
  });

  // TODO bring back when we have a no recent data message
  it.skip('asserts countryPanel contains "no-recent-data" message', () => {
    cy.interceptAPI('v9/details/hourly_72/UA');
    cy.visit('/zone/UA?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.waitForAPISuccess('v9/state/hourly_72');
    cy.waitForAPISuccess('v9/details/hourly_72/UA');

    cy.get('[data-testid=no-data-overlay-message]')
      .should('exist')
      .contains('Data is temporarily unavailable for the selected time');
  });

  it('asserts countryPanel contains no parser message when zone has no data', () => {
    // Add all required API intercepts
    cy.interceptAPI('v9/state/hourly_72');
    cy.interceptAPI('v9/details/hourly_72/CN');
    cy.interceptAPI('v9/meta'); // Add this if needed

    cy.visit('/zone/CN/72h?lang=en-GB', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });

    cy.waitForAPISuccess('v9/state/hourly_72');
    cy.waitForAPISuccess('v9/details/hourly_72/CN');

    cy.get('[data-testid=no-parser-message]').should('exist');
  });

  // TODO(AVO-659): fix flaky tests
  it.skip('scrolls to anchor element if provided a hash in url', () => {
    cy.interceptAPI('v9/details/hourly_72/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB#origin_chart', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-testid=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly_72');
    cy.waitForAPISuccess('v9/details/hourly_72/DK-DK2');
    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('#origin_chart').should('be.visible');
  });

  it.skip('scrolls to anchor element if provided a hash with caps in url', () => {
    cy.interceptAPI('v9/details/hourly_72/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB#oRiGiN_ChArT', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-testid=close-modal]').click();
    // cy.waitForAPISuccess('v9/state/hourly_72');
    cy.waitForAPISuccess('v9/details/hourly_72/DK-DK2');
    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('#origin_chart').should('be.visible');
  });

  it('does not scroll or error if provided a non-sensical hash in url', () => {
    cy.interceptAPI('v9/details/hourly_72/DK-DK2');

    cy.visit('/zone/DK-DK2?lang=en-GB##not-a-thing', {
      onBeforeLoad(win) {
        delete win.navigator.__proto__.serviceWorker;
      },
    });
    cy.get('[data-testid=close-modal]').click();
    cy.waitForAPISuccess('v9/state/hourly_72');
    cy.waitForAPISuccess('v9/details/hourly_72/DK-DK2');
    cy.get('[data-testid=left-panel] [data-testid=co2-square-value]').should(
      'be.visible'
    );
  });
});
