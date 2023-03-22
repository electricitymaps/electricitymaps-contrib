// TODO: Convert to component test
// TODO: Uncomment tests
describe('Map', () => {
  it('interacts with the map', () => {
    cy.interceptAPI('v6/state/hourly');
    cy.visit('/?lang=en-GB');
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess(`v6/state/hourly`);
    cy.get('[data-test-id=loading-overlay]').should('not.exist');

    // closes left panel
    cy.get('[data-test-id=left-panel-collapse-button]').click();

    // tests toggle
    cy.contains('production').click();
    cy.contains('consumption').click();

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

    // test zoom buttons

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

    // eslint-disable-next-line cypress/require-data-selectors
    cy.get('.maplibregl-ctrl-zoom-in.mapboxgl-ctrl-zoom-in').click();
  });
});
