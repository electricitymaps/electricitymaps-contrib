import { TFunction } from 'i18next';
import { useAtom } from 'jotai';
import { resolvePath, useSearchParams } from 'react-router-dom';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';

import Modal, { Page } from './OnboardingModalInner';

interface ViewContentProps {
  t: TFunction;
  translationKey: string;
  isDangerouslySet?: boolean;
}

const HEADER_STYLE = 'mb-2 px-2 text-base font-semibold sm:text-lg sm:mb-4';
const BODY_STYLE = 'text-sm px-4 sm:text-base pb-4';

function ViewContent({ t, translationKey, isDangerouslySet = false }: ViewContentProps) {
  return (
    <>
      <div>
        <h2 className={HEADER_STYLE}>{t(`${translationKey}.header`)}</h2>
      </div>
      {isDangerouslySet ? (
        <p
          dangerouslySetInnerHTML={{
            __html: t(`${translationKey}.text`),
          }}
          className={BODY_STYLE}
        ></p>
      ) : (
        <div className={BODY_STYLE}>{t(`${translationKey}.text`)}</div>
      )}
    </>
  );
}

const views: Page[] = [
  {
    headerImage: resolvePath('images/electricitymaps-icon.svg'),
    isMainTitle: true,
    renderContent: (t) => (
      <ViewContent t={t} translationKey="onboarding-modal.view1" isDangerouslySet />
    ),
  },
  {
    headerImage: resolvePath('images/onboarding/mapExtract'),
    hasWebp: true,
    renderContent: (t) => <ViewContent t={t} translationKey="onboarding-modal.view2" />,
  },
  {
    headerImage: resolvePath('images/onboarding/exchangeArrows.gif'),
    renderContent: (t) => <ViewContent t={t} translationKey="onboarding-modal.view3" />,
  },
  {
    headerImage: resolvePath('images/onboarding/switchViews'),
    hasWebp: true,
    renderContent: (t) => <ViewContent t={t} translationKey="onboarding-modal.view4" />,
  },
  {
    headerImage: resolvePath('images/onboarding/switchEmissions'),
    hasWebp: true,
    renderContent: (t) => <ViewContent t={t} translationKey="onboarding-modal.view5" />,
  },
  {
    headerImage: resolvePath('images/onboarding/pastData'),
    hasWebp: true,
    renderContent: (t) => <ViewContent t={t} translationKey="onboarding-modal.view6" />,
  },
  {
    headerImage: resolvePath('images/onboarding/splitLayers'),
    hasWebp: true,
    renderContent: (t) => <ViewContent t={t} translationKey="onboarding-modal.view7" />,
  },
];

export function OnboardingModal() {
  const [hasOnboardingBeenSeen, setHasOnboardingBeenSeen] = useAtom(
    hasOnboardingBeenSeenAtom
  );
  const [searchParameters] = useSearchParams();
  const skipOnboarding = searchParameters.get('skip-onboarding') === 'true';
  const visible = !hasOnboardingBeenSeen && !skipOnboarding;
  const handleDismiss = () => {
    setHasOnboardingBeenSeen(true);
  };
  return (
    <Modal
      modalName="onboarding"
      data-test-id="onboarding"
      visible={visible}
      onDismiss={handleDismiss}
      views={views}
    />
  );
}
