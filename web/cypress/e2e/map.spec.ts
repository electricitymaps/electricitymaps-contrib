// TODO: Convert to component test
// TODO: Uncomment tests
describe('Map', () => {
  it('interacts with the map', () => {
    cy.interceptAPI('v8/state/hourly');
    cy.visit('/?lang=en-GB');
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess(`v8/state/hourly`);
    cy.get('[data-test-id=loading-overlay]').should('not.exist');

    // test map
    cy.get('[data-test-id=exchange-layer]').should('exist');
    cy.get('[data-test-id=wind-layer]').should('exist');
    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('.maplibregl-map').should('be.visible');

    // Close the info according on the ranking panel
    cy.get('[data-test-id=collapse-button]').click();

    cy.get('[data-test-id=zone-search-bar]').type('Denmark');
    cy.get('[data-index="0"] > .group').click();
    // Check that the page title contains the zone name
    cy.title().should('contain', 'Bornholm');

    cy.get('[data-test-id=left-panel-back-button]').click();

    // closes left panel
    cy.get('[data-test-id=left-panel-collapse-button]').click();

    // tests toggle
    cy.get('[data-test-id=toggle-button-production-toggle]').click();
    cy.get('[data-test-id=exchange-arrow-DK-DK2-\\>SE-SE4]').should('not.exist');
    cy.get('[data-test-id=toggle-button-consumption-toggle]').click();

    // TODO: functionality has changed to be an onhover trigger
    // rather than a click trigger for the tooltip. This may cause issues for mobile?

    // cy.contains('takes imports and exports into account,').should(
    //   'have.css',
    //   'visibility',
    //   'visible'
    // );
    // cy.contains('takes imports and exports into account,').should(
    //   'have.css',
    //   'visibility',
    //   'hidden'
    // );

    // test language selector
    cy.get('[data-test-id=language-selector-open-button]').click();
    cy.contains('English');
    cy.contains('Dansk').click();
    cy.contains('forbrug');
    // cy.get('[data-test-id=language-selector]').click();
    // cy.contains('English').click();
    // cy.contains('consumption');

    // test layers

    cy.get('[data-test-id=wind-layer-button]').should('be.visible').click();
    // cy.contains('Wind power potential');

    cy.get('[data-test-id=solar-layer-button]').should('be.visible').click();
    // cy.contains('Solar power potential');

    // test dark mode
    // cy.get('[data-test-id=dark-mode-button]').click().click();

    // test zoom buttons
    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('.maplibregl-ctrl-zoom-in.maplibregl-ctrl-zoom-in').click();

    // test exchange arrows
    cy.get('[data-test-id=exchange-arrow-DK-DK2-\\>SE-SE4]').should('be.visible');

    // toggle to country view
    cy.get('[data-test-id=toggle-button-country-toggle]').click();

    // test exchange arrows
    cy.get('[data-test-id=exchange-arrow-DK-\\>SE]').should('be.visible');

    // toggle back to zone view
    cy.get('[data-test-id=toggle-button-zone-toggle]').click();

    // closes left panel
    cy.get('[data-test-id=left-panel-collapse-button]').click();

    cy.get('[data-test-id=zone-search-bar]').type('Japan');
    cy.get('[data-index="0"] > .group').click();

    cy.get('[data-test-id=exchange-arrow-JP-TH-\\>JP-TK]').should('be.visible');
  });
});
