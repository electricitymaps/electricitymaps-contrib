// TODO: Convert to component test
describe('Map', () => {
  it('interacts with the map', () => {
    cy.interceptAPI('v5/state/hourly');
    cy.visit('/?skip-onboarding=true&lang=en-GB');
    cy.waitForAPISuccess(`v5/state/hourly`);

    // closes left panel
    cy.get('[data-test-id=left-panel-collapse-button]').click();

    // tests toggle
    cy.contains('production').click();
    cy.contains('consumption').click();
    // TODO: cy.get('.controls-container > div > div:nth-child(2)').contains('i').click();
    cy.contains('takes imports and exports into account,').should('have.css', 'visibility', 'visible');
    // TODO: cy.get('.controls-container > div > div:nth-child(2)').contains('i').click();
    cy.contains('takes imports and exports into account,').should('have.css', 'visibility', 'hidden');

    // test zoom buttons
    cy.get('[data-test-id=mapboxgl-ctrl-zoom-in]').click();
    cy.get('[data-test-id=mapboxgl-ctrl-zoom-out]').click();

    // test language selector
    cy.get('[data-test-id=language-selector]').click();
    cy.contains('Dansk').click();
    cy.contains('forbrug');
    cy.get('[data-test-id=language-selector]').click();
    cy.contains('English').click();
    cy.contains('consumption');

    // test layers
    cy.get('[data-test-id=wind-layer-button]').should('be.visible').click();
    cy.contains('Wind power potential');

    cy.get('[data-test-id=solar-layer-button]').should('be.visible').click();
    cy.contains('Solar power potential');

    // test dark mode
    cy.get('[data-test-id=dark-mode-button]').click().click();
  });
});
