describe('Map', () => {
  it('interacts with the map', () => {
    cy.visit('/');
    // sees modal and closes it
    cy.get('[data-test-id=onboarding]').get('.modal-close-button').click();

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
    cy.get('[href="/map?wind=true"]').click();
    cy.contains('Wind power potential');
    // TODO: For some reason the link is not "mounted in DOM" until after a while...
    // Dunno how to solve it without avoid adding this delay
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(200);
    cy.get('a[href*="solar=true"]').click();
    cy.contains('Solar power potential');

    // test dark mode
    cy.get('[aria-label="Toggle dark-mode"]').click().click();
  });
});
