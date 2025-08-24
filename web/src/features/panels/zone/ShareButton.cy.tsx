import { Capacitor } from '@capacitor/core';
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

  it('should display copy button on desktop web', () => {
    cy.stub(Capacitor, 'isNativePlatform').returns(false);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="linkIcon"]').should('be.visible');
    cy.get('[data-testid="iosShareIcon"]').should('not.exist');
    cy.get('[data-testid="defaultShareIcon"]').should('not.exist');
  });

  it('should display share icon for iOS native app', () => {
    cy.stub(Capacitor, 'isNativePlatform').returns(true);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={true} hasMobileUserAgent={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="iosShareIcon"]').should('be.visible');
    cy.get('[data-testid="defaultShareIcon"]').should('not.exist');
    cy.get('[data-testid="linkIcon"]').should('not.exist');
  });

  it('should display share icon for iOS mobile web', () => {
    cy.stub(Capacitor, 'isNativePlatform').returns(false);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={true} hasMobileUserAgent={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="iosShareIcon"]').should('be.visible');
    cy.get('[data-testid="defaultShareIcon"]').should('not.exist');
    cy.get('[data-testid="linkIcon"]').should('not.exist');
  });

  it('should display default share icon for non-iOS native app', () => {
    cy.stub(Capacitor, 'isNativePlatform').returns(true);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} hasMobileUserAgent={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="defaultShareIcon"]').should('be.visible');
    cy.get('[data-testid="iosShareIcon"]').should('not.exist');
    cy.get('[data-testid="linkIcon"]').should('not.exist');
  });

  it('should display default share icon for non-iOS mobile web', () => {
    cy.stub(Capacitor, 'isNativePlatform').returns(false);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} hasMobileUserAgent={true} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="defaultShareIcon"]').should('be.visible');
    cy.get('[data-testid="iosShareIcon"]').should('not.exist');
    cy.get('[data-testid="linkIcon"]').should('not.exist');
  });

  it('should trigger toast on click', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="share-btn"]').should('exist');
    cy.get('[data-testid="toast"]').should('not.exist');
    cy.get('[data-testid="share-btn"]').click();
    cy.get('[data-testid="toast"]').should('exist');
  });

  it('should close toast on click', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ShareButton showIosIcon={false} />
        </ToastProvider>
      </QueryClientProvider>
    );
    cy.get('[data-testid="share-btn"]').click();
    cy.get('[data-testid="toast"]').should('be.visible');
    cy.get('[data-testid="toast-dismiss"]').click();
    cy.get('[data-testid="toast"]').should('not.exist');
  });
});
