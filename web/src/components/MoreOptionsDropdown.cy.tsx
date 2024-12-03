import { ToastProvider } from '@radix-ui/react-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Ellipsis } from 'lucide-react';
import { I18nextProvider } from 'react-i18next';
import { BrowserRouter } from 'react-router-dom';
import i18n from 'translation/i18n';
import { Charts } from 'utils/constants';

import { MoreOptionsDropdown } from './MoreOptionsDropdown';

const queryClient = new QueryClient();

function Providers({ children }: { children: React.ReactElement }) {
  return (
    <BrowserRouter>
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <ToastProvider>
            <div className="ml-72">{children}</div>
          </ToastProvider>
        </QueryClientProvider>
      </I18nextProvider>
    </BrowserRouter>
  );
}

describe('MoreOptionsDropdown', () => {
  beforeEach(() => {
    cy.intercept('/feature-flags', {
      body: { 'more-options-dropdown': true },
    });
  });

  it('opens dropdown on trigger click', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={true}
          shareUrl="hello"
          isEstimated={false}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );

    cy.get('button').should('be.visible');
    cy.get('button').click();
    cy.contains('Preliminary data may change over time.').should('not.exist');
  });

  it('closes on dismiss', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={true}
          shareUrl="hello"
          isEstimated={false}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );
    cy.get('button').click();
    cy.contains('Share').should('be.visible');
    cy.get('[data-testid=dismiss-btn]').click();
    cy.get('Share').should('not.exist');
  });

  it('displays mobile share options on mobile', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={true}
          shareUrl="hello"
          isEstimated={false}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );
    cy.get('button').click();
    cy.contains('Share via').should('be.visible');
    cy.contains('Share on X (Twitter)').should('not.exist');
    cy.get('Share on LinkedIn').should('not.exist');
    cy.get('Share on Facebook').should('not.exist');
  });

  it('displays social media share options on desktop', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={false}
          shareUrl="hello"
          isEstimated={false}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );

    cy.get('button').click();
    cy.get('Share via').should('not.exist');

    cy.contains('Share on X (Twitter)').should('be.visible');
    cy.get('[data-testid=twitter-chart-share]')
      .should('have.attr', 'href')
      .and(
        'equal',
        'https://twitter.com/intent/tweet?&url=hello&text=Discover%20real-time%20electricity%20insights%20with%20the%20Electricity%20Maps%20app!%20https://app.electricitymaps.com&hashtags=electricitymaps'
      );

    cy.contains('Share on LinkedIn').should('be.visible');
    cy.get('[data-testid=linkedin-chart-share]')
      .should('have.attr', 'href')
      .and('equal', 'https://www.linkedin.com/shareArticle?mini=true&url=hello');

    cy.contains('Share on Facebook').should('be.visible');
    cy.get('[data-testid=facebook-chart-share]')
      .should('have.attr', 'href')
      .and(
        'equal',
        'https://facebook.com/sharer/sharer.php?u=hello&quote=Discover%20real-time%20electricity%20insights%20with%20the%20Electricity%20Maps%20app!%20https://app.electricitymaps.com'
      );

    cy.contains('Share on Reddit').should('be.visible');
    cy.get('[data-testid=reddit-chart-share]')
      .should('have.attr', 'href')
      .and('equal', 'https://www.reddit.com/web/submit?url=hello');
  });

  it('displays preliminary data warning', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={false}
          shareUrl="hello"
          isEstimated={true}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );
    cy.get('button').click();
    cy.contains('Preliminary data may change over time.').should('be.visible');
  });

  it('should trigger toast on click', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={false}
          shareUrl="hello"
          isEstimated={true}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );
    cy.get('button').click();
    cy.contains('Copy link to chart').should('exist');
    cy.get('[data-testid="toast"]').should('not.exist');
    cy.contains('Copy link to chart').click();
    cy.get('[data-testid="toast"]').should('exist');
  });

  it('should close toast on click', () => {
    cy.mount(
      <Providers>
        <MoreOptionsDropdown
          hasMobileUserAgent={false}
          shareUrl="hello"
          isEstimated={true}
          id={Charts.ORIGIN_CHART}
        >
          <Ellipsis />
        </MoreOptionsDropdown>
      </Providers>
    );
    cy.get('button').click();
    cy.contains('Copy link to chart').click();
    cy.get('[data-testid="toast"]').should('be.visible');
    cy.get('[data-testid="toast-dismiss"]').click();
    cy.get('[data-testid="toast"]').should('not.exist');
  });
});
