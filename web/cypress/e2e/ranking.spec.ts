// TODO: Convert to component test
describe('Ranking Panel', () => {
  it('interacts with details', () => {
    cy.interceptAPI('v5/state/hourly');
    cy.visit('/?skip-onboarding=true&lang=en-GB');
    cy.waitForAPISuccess(`v5/state/hourly`);

    // See more than X countries on the list by default
    cy.get('[data-test-id=zone-list-link]').should('have.length.above', 3);

    // Search for a country
    cy.get('[data-test-id=zone-search-bar]').type('Germ');
    cy.get('[data-test-id=zone-list-link]').should('have.length', 1);

    // Click a country and return the the ranking panel
    cy.get('[data-test-id=zone-list-link-selected]').click();
    cy.get('[data-test-id=left-panel] [data-test-id=zone-name]').should('exist');
    cy.get('[data-test-id=left-panel-back-button]').click({ force: true });

    // TODO: Ideally the search result should either be reset or the typed value stay in the input

    // enable colorblind mode
    cy.get('[data-test-id=colorblind-checkbox]').check({ force: true });

    // open faq
    cy.get('[data-test-id=faq-link]').click();
    cy.contains('Frequently Asked Questions');
    cy.get('[data-test-id=left-panel-back-button]').click();
  });
});
