import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import { BrowserRouter } from 'react-router-dom';
import i18n from 'translation/i18n';

import { OnboardingModal } from './OnboardingModal';

const queryClient = new QueryClient();

describe('OnboardingModal', () => {
  beforeEach(() => {
    cy.intercept('/feature-flags', {
      body: { 'consumption-only': false },
    });
  });
  it('mounts', () => {
    cy.mount(
      <QueryClientProvider client={queryClient}>
        <I18nextProvider i18n={i18n}>
          <BrowserRouter>
            <OnboardingModal />
          </BrowserRouter>
        </I18nextProvider>
      </QueryClientProvider>
    );
    cy.contains('Electricity Maps');
  });
});
