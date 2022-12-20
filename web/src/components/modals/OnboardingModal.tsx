import { resolvePath, useParams } from 'react-router-dom';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';

import Modal from './OnboardingModalInner';
import { useAtom } from 'jotai';

const views = [
  {
    headerImage: resolvePath('electricitymaps-icon.svg'),
    isMainTitle: true,
    renderContent: (__: (translationKey: string) => string) => (
      <>
        <div>
          <h1 className="text-2xl">Electricity Maps</h1>
        </div>
        <div className=" py-6 text-xl">
          <h2>{__('onboarding-modal.view1.subtitle')}</h2>
        </div>
      </>
    ),
  },
  {
    headerImage: resolvePath('onboarding/mapExtract.png'),
    renderContent: (__: (translationKey: string) => string) => (
      <>
        <div>
          <h2 className="text-xl">{__('onboarding-modal.view2.header')}</h2>
        </div>
        <div>{__('onboarding-modal.view2.text')}</div>
      </>
    ),
  },
  {
    headerImage: resolvePath('onboarding/exchangeArrows.png'),
    renderContent: (__: (translationKey: string) => string) => (
      <>
        <div>
          <h2 className="text-xl">{__('onboarding-modal.view3.header')}</h2>
        </div>
        <div>{__('onboarding-modal.view3.text')}</div>
      </>
    ),
  },
  {
    headerImage: resolvePath('onboarding/splitLayers.png'),
    renderContent: (__: (translationKey: string) => string) => (
      <>
        <div>
          <h2 className="text-xl">{__('onboarding-modal.view4.header')}</h2>
        </div>
        <div>{__('onboarding-modal.view4.text')}</div>
      </>
    ),
  },
];

export function OnboardingModal() {
  const { skipOnboarding } = useParams();
  const [hasOnboardingBeenSeen, setHasOnboardingBeenSeen] = useAtom(
    hasOnboardingBeenSeenAtom
  );
  const visible = !hasOnboardingBeenSeen && !skipOnboarding;

  const handleDismiss = () => {
    setHasOnboardingBeenSeen('true');
  };
  return (
    <Modal
      modalName="onboarding"
      visible={visible}
      onDismiss={handleDismiss}
      views={views}
    />
  );
}
