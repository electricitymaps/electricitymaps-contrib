import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'jotai';
import { I18nextProvider } from 'react-i18next';

import i18n from '../../translation/i18n';
import { SettingsModalContent } from './SettingsModal';

describe('SettingsModalContent', () => {
  const queryClient = new QueryClient();

  it('displays settings content', () => {
    cy.viewport(500, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <Provider>
          <I18nextProvider i18n={i18n}>
            <SettingsModalContent />
          </I18nextProvider>
        </Provider>
      </QueryClientProvider>
    );

    // Check for key elements in the settings modal
    cy.contains('Language').should('exist');
    cy.contains('country').should('exist');
    cy.contains('zone').should('exist');
  });

  it('displays theme options', () => {
    cy.viewport(500, 500);
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <Provider>
          <I18nextProvider i18n={i18n}>
            <SettingsModalContent />
          </I18nextProvider>
        </Provider>
      </QueryClientProvider>
    );

    // Check if theme toggle buttons exist by looking for their container
    cy.get('div.flex.space-x-1').should('exist');

    // Check if there are at least 3 buttons (light, dark, system)
    cy.get('div.flex.space-x-1 > button').should('have.length.at.least', 3);

    // Set up localStorage spy
    cy.window().then((win) => {
      cy.spy(win.localStorage, 'setItem').as('setItem');
    });

    // Click the first theme button (should be light theme)
    cy.get('div.flex.space-x-1 > button').first().click();

    // Verify localStorage was called with theme
    cy.get('@setItem').should('be.calledWith', 'theme');
  });
});
