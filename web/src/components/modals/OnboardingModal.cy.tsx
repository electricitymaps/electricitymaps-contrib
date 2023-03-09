import { OnboardingModal } from './OnboardingModal';

it('mounts', () => {
  cy.mount(<OnboardingModal isComponentTest={true} />);
  cy.contains('Electricity Maps');
});
