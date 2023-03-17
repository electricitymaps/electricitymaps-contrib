import { BrowserRouter } from 'react-router-dom';
import { OnboardingModal } from './OnboardingModal';

it('mounts', () => {
  cy.mount(
    <BrowserRouter>
      <OnboardingModal />
    </BrowserRouter>
  );
  cy.contains('Electricity Maps');
});
