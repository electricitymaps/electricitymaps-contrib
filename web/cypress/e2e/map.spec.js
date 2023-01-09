describe('Map', () => {
  it('interacts with the map', () => {
    cy.interceptAPI('v5/state/hourly');
    cy.visit('/?skip-onboarding=true&lang=en-GB');
    cy.waitForAPISuccess(`v5/state/hourly`);

    // closes left panel
    cy.get('#left-panel-collapse-button').click();

    // tests toggle
    cy.contains('production').click();
    cy.contains('consumption').click();
    cy.get('.controls-container > div > div:nth-child(2)').contains('i').click();
    cy.contains('takes imports and exports into account,').should('have.css', 'visibility', 'visible');
    cy.get('.controls-container > div > div:nth-child(2)').contains('i').click();
    cy.contains('takes imports and exports into account,').should('have.css', 'visibility', 'hidden');

    // test zoom buttons
    cy.get('.mapboxgl-ctrl-zoom-in').click();
    cy.get('.mapboxgl-ctrl-zoom-out').click();

    // test language selector
    cy.get('[aria-label="Select language"]').click();
    cy.contains('Dansk').click();
    cy.contains('forbrug');
    cy.get('[aria-label="Skift sprog"]').click();
    cy.contains('English').click();
    cy.contains('consumption');

    // test layers
    cy.get('a[href*="wind=true"]').should('be.visible').click();
    cy.contains('Wind power potential');

    cy.get('a[href*="solar=true"]').should('be.visible').click();
    cy.contains('Solar power potential');

    // test dark mode
    cy.get('[aria-label="Toggle dark-mode"]').click().click();
  });
});
