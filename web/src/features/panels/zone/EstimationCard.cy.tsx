import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import EstimationCard from './EstimationCard';

const queryClient = new QueryClient();

describe('EstimationCard', () => {
  beforeEach(() => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <EstimationCard
          cardType="estimated"
          estimationMethod="ESTIMATED_CONSTRUCT_BREAKDOWN"
          outageMessage={undefined}
        />
      </QueryClientProvider>
    );
  });

  it('feedback card should only be visible when collapse button has been clicked', () => {
    cy.intercept('/feature-flags', {
      body: { 'feedback-estimation-labels': true },
    });
    cy.get('[data-test-id=feedback-card]').should('not.exist');
    cy.get('[data-test-id=collapse-button]').click();
    cy.get('[data-test-id=feedback-card]').should('exist');
    cy.get('[data-test-id=collapse-button]').click();
    cy.get('[data-test-id=feedback-card]').should('exist');
  });
  it('feedback card should only be visible if feature-flag is enabled', () => {
    cy.intercept('/feature-flags', {
      body: { 'feedback-estimation-labels': false },
    });
    cy.get('[data-test-id=feedback-card]').should('not.exist');
    cy.get('[data-test-id=collapse-button]').click();
    cy.get('[data-test-id=feedback-card]').should('exist');
  });
});
