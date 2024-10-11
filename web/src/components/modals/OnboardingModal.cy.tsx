import { I18nextProvider } from 'react-i18next';
import { BrowserRouter } from 'react-router-dom';
import i18n from 'translation/i18n';

import { OnboardingModal } from './OnboardingModal';

it('mounts', () => {
  cy.mount(
    <I18nextProvider i18n={i18n}>
      <BrowserRouter>
        <OnboardingModal />
      </BrowserRouter>
    </I18nextProvider>
  );
  cy.contains('Electricity Maps');
});
