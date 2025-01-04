import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
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
    function ModalWrapper() {
      return (
        <QueryClientProvider client={queryClient}>
          <I18nextProvider i18n={i18n}>
            <OnboardingModal />
          </I18nextProvider>
        </QueryClientProvider>
      );
    }

    const router = createMemoryRouter(
      [
        {
          path: '*',
          element: <ModalWrapper />,
        },
      ],
      {
        initialEntries: ['/'],
      }
    );

    cy.mount(<RouterProvider router={router} />);
    cy.contains('Electricity Maps');
  });
});
