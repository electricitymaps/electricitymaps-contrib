describe('Ranking Panel', () => {
  it('interacts with details', () => {
    cy.interceptAPI('v5/state/hourly');
    cy.visit('/?skip-onboarding=true&lang=en-GB');
    cy.waitForAPISuccess(`v5/state/hourly`);

    // See more than X countries on the list by default
    cy.get('.zone-list a').should('have.length.above', 3);

    // Search for a country
    cy.get('.zone-search-bar > input').type('Germ');
    cy.get('.zone-list a').should('have.length', 1);

    // Click a country and return the the ranking panel
    cy.get('.zone-list a.selected').click();
    cy.get('.left-panel-zone-details .country-name').should('exist');
    cy.get('.left-panel-back-button').click({ force: true });

    // TODO: Ideally the search result should either be reset or the typed value stay in the input

    // enable colorblind mode
    cy.get('#checkbox-colorblind').check({ force: true });

    // open faq
    cy.get('a[href^="/faq"]').click();
    cy.contains('Frequently Asked Questions');
    cy.get('.left-panel-back-button').click();
  });
});
