import EstimationCard from './EstimationCard';

describe('EstimationCard', () => {
  beforeEach(() => {
    cy.mount(
      <EstimationCard
        cardType="estimated"
        estimationMethod="ESTIMATED_CONSTRUCT_BREAKDOWN"
        outageMessage={undefined}
      />
    );
  });

  it('feedback card should only be visible when collapse button has been clicked twice or more', () => {
    cy.get('[data-test-id=feedback-card]').should('not.exist');
    cy.get('[data-test-id=collapse-button]').click();
    cy.get('[data-test-id=feedback-card]').should('exist');
    cy.get('[data-test-id=collapse-button]').click();
    cy.get('[data-test-id=feedback-card]').should('exist');
  });
});
