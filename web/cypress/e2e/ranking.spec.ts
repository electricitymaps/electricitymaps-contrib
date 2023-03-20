// TODO: Convert to component test and uncomment test
describe('Ranking Panel', () => {
  it('interacts with details', () => {
    cy.interceptAPI('v6/state/hourly');
    cy.interceptAPI('v6/details/hourly/DK-DK2');
    cy.visit('/?lang=en-GB');
    cy.get('[data-test-id=close-modal]').click();
    cy.waitForAPISuccess(`v6/state/hourly`);
    cy.get('[data-test-id=loading-overlay]').should('not.exist');
    // See more than X countries on the list by default
    cy.get('[data-test-id=zone-list-link]').should('have.length.above', 3);

    // Search for a country
    cy.get('[data-test-id=zone-search-bar]').type('east denm');
    cy.get('[data-test-id=zone-list-link]').should('have.length', 1);

    // Click a country and return the the ranking panel
    cy.get('[data-test-id=zone-list-link]').click();
    cy.get('[data-test-id=zone-name]').should('exist');
    cy.get('[data-test-id=left-panel-back-button]').click();

    // TODO: Ideally the search result should either be reset or the typed value stay in the input

    // enable colorblind mode
    // cy.get('[data-test-id=colorblind-checkbox]').check({ force: true });

    // open faq
    // cy.get('[data-test-id=faq-link]').click();
    // cy.contains('Frequently Asked Questions');
    // cy.get('[data-test-id=left-panel-back-button]').click();
  });
});
