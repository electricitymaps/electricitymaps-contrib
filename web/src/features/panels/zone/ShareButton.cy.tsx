import { ToastProvider } from '@radix-ui/react-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ShareButton } from './ShareButton';

const queryClient = new QueryClient();

describe('Share Button', () => {
  beforeEach(() => {
    cy.intercept('/feature-flags', {
      body: { 'share-button': true },
    });
  });

  it('should display share icon for iOS', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showiOSIcon={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="iosShareIcon"]').should('be.visible');
    cy.get('[data-test-id="defaultShareIcon"]').should('not.exist');
  });

  it('should display default share icon', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showiOSIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="defaultShareIcon"]').should('be.visible');
    cy.get('[data-test-id="iosShareIcon"]').should('not.exist');
  });

  it('should trigger toast on click', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showiOSIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="share-btn"]').should('exist');
    cy.get('[data-test-id="toast"]').should('not.exist');
    cy.get('[data-test-id="share-btn"]').click();
    cy.get('[data-testid="toast"]').should('exist');
  });
});
