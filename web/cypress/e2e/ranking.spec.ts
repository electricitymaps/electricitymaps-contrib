// TODO: Convert to component test and uncomment test
describe('Ranking Panel', () => {
  it('interacts with details', () => {
    cy.interceptAPI('v10/meta');
    cy.interceptAPI('v10/state/hourly');
    cy.interceptAPI('v10/details/hourly/DK-DK2');
    cy.visit('/?lang=en-GB');
    cy.get('[data-testid=close-modal]').click();
    cy.waitForAPISuccess(`v10/meta`);
    cy.waitForAPISuccess(`v10/state/hourly`);
    cy.get('[data-testid=loading-overlay]').should('not.exist');

    // Close the ranking panel accordion
    cy.get('[data-testid=collapse-button]').click();

    // See more than X countries on the list by default
    cy.get('[data-testid=zone-list-link]').should('have.length.above', 3);

    // Search for a country
    cy.get('[data-testid=zone-search-bar]').type('east denm');
    cy.get('[data-testid=zone-list-link]').should('have.length', 1);

    // Click a country and return the the ranking panel
    cy.get('[data-testid=zone-list-link]').click();
    cy.get('[data-testid=zone-name]').should('exist');
    cy.get('[data-testid=left-panel-back-button]').click();

    // TODO: Ideally the search result should either be reset or the typed value stay in the input

    // enable colorblind mode
    // cy.get('[data-testid=colorblind-checkbox]').check({ force: true });

    // open faq
    // cy.get('[data-testid=faq-link]').click();
    // cy.contains('Frequently Asked Questions');
    // cy.get('[data-testid=left-panel-back-button]').click();
  });
});
