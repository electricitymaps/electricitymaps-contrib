import { OnboardingModal } from './OnboardingModal';

it('mounts', () => {
  cy.mount(<OnboardingModal />);
  cy.contains('Electricity Maps');
});
