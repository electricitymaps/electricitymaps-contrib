import { Capacitor } from '@capacitor/core';
import { ToastProvider } from '@radix-ui/react-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { s } from 'vite/dist/node/types.d-aGj9QkWt';

import { ShareButton } from './ShareButton';

const queryClient = new QueryClient();

describe.skip('Share Button', () => {
  beforeEach(() => {
    cy.intercept('/feature-flags', {
      body: { 'share-button': true },
    });
    cy.stub(Capacitor, 'isNativePlatform').returns(true);
  });

  it('should display copy button on desktop web', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="linkIcon"]').should('be.visible');
    cy.get('[data-test-id="iosShareIcon"]').should('not.exist');
    cy.get('[data-test-id="defaultShareIcon"]').should('not.exist');
  });

  it('should display share icon for iOS native app', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="iosShareIcon"]').should('be.visible');
    cy.get('[data-test-id="defaultShareIcon"]').should('not.exist');
    cy.get('[data-test-id="linkIcon"]').should('not.exist');
  });

  it('should display share icon for iOS mobile web', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="iosShareIcon"]').should('be.visible');
    cy.get('[data-test-id="defaultShareIcon"]').should('not.exist');
    cy.get('[data-test-id="linkIcon"]').should('not.exist');
  });

  it('should display default share icon for non-iOS native app', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="defaultShareIcon"]').should('be.visible');
    cy.get('[data-test-id="iosShareIcon"]').should('not.exist');
    cy.get('[data-test-id="linkIcon"]').should('not.exist');
  });

  it('should display default share icon for non-iOS mobile web', () => {
    cy.stub(Capacitor, 'isNativePlatform').returns(false);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="defaultShareIcon"]').should('be.visible');
    cy.get('[data-test-id="iosShareIcon"]').should('not.exist');
    cy.get('[data-test-id="linkIcon"]').should('not.exist');
  });

  it('should trigger toast on click', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="share-btn"]').should('exist');
    cy.get('[data-test-id="toast"]').should('not.exist');
    cy.get('[data-test-id="share-btn"]').click();
    cy.get('[data-testid="toast"]').should('exist');
  });

  it('should close toast on click', () => {
    s;
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-test-id="share-btn"]').click();
    cy.get('[data-testid="toast"]').should('be.visible');
    cy.get('[data-testid="toast-dismiss"]').click();
    cy.get('[data-testid="toast"]').should('not.exist');
  });
});
