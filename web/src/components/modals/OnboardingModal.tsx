import { Button } from 'components/Button';
import Modal from 'components/Modal';
import { useFeatureFlag } from 'features/feature-flags/api';
import { TFunction } from 'i18next';
import { useAtom } from 'jotai';
import { Check, ChevronLeft, ChevronRight } from 'lucide-react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { resolvePath, useSearchParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';

interface ViewContentProps {
  t: TFunction;
  translationKey: string;
  isDangerouslySet?: boolean;
}

const TOGGLE_MODE_IDX = 3;
const BODY_STYLE = 'text-sm px-4 sm:text-base pb-4';

function ViewContent({ t, translationKey, isDangerouslySet = false }: ViewContentProps) {
  return (
    <>
      <h1 className="mb-4">{t(`${translationKey}.header`)}</h1>
      {isDangerouslySet ? (
        <p
          dangerouslySetInnerHTML={{
            __html: t(`${translationKey}.text`),
          }}
          className={BODY_STYLE}
        />
      ) : (
        <p className={BODY_STYLE}>{t(`${translationKey}.text`)}</p>
      )}
    </>
  );
}

interface HeaderImageProps {
  image: { pathname: string };
  hasWebp?: boolean;
  isMainTitle?: boolean;
  isFirstView?: boolean;
}

function HeaderImage({ image, hasWebp, isMainTitle, isFirstView }: HeaderImageProps) {
  if (!hasWebp) {
    return (
      <div
        className={twMerge(
          'w-full',
          isFirstView &&
            'mx-auto max-w-[80%] self-center bg-center bg-no-repeat dark:invert'
        )}
        style={{
          backgroundImage: `url("${image.pathname}")`,
          backgroundSize: isMainTitle ? 'contain' : 'cover',
          height: '100%',
        }}
      />
    );
  }

  return (
    <picture className="h-full w-full overflow-hidden">
      <source srcSet={`${image.pathname}.webp`} type="image/webp" />
      <img
        src={`${image.pathname}.png`}
        alt=""
        className="h-full w-full  object-cover"
        draggable={false}
      />
    </picture>
  );
}

interface NavigationDotsProps {
  totalViews: number;
  currentIndex: number;
  onChange: (index: number) => void;
}

function NavigationDots({ totalViews, currentIndex, onChange }: NavigationDotsProps) {
  return (
    <div className="absolute -bottom-8 left-1/2 flex -translate-x-1/2 space-x-4">
      {Array.from({ length: totalViews }).map((_, index) => (
        <button
          key={`modal-step-item-${index}`}
          className={twMerge(
            'h-3.5 w-3.5 rounded-full transition-colors',
            index === currentIndex
              ? 'bg-brand-green dark:bg-brand-green-dark'
              : 'bg-white dark:bg-neutral-400/80'
          )}
          onClick={() => onChange(index)}
        />
      ))}
    </div>
  );
}

interface Page {
  headerImage: { pathname: string };
  isMainTitle?: boolean;
  renderContent: (translator: TFunction) => React.ReactElement;
  hasWebp?: boolean;
}

const views: Page[] = [
  {
    headerImage: resolvePath('images/electricity-maps-logo.svg'),
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

interface OnboardingModalContentProps {
  currentView: Page;
  isOnFirstView: boolean;
  isOnLastView: boolean;
  currentViewIndex: number;
  totalViews: number;
  onBack: () => void;
  onForward: () => void;
  onNavigate: (index: number) => void;
}

function OnboardingModalContent({
  currentView,
  isOnFirstView,
  isOnLastView,
  currentViewIndex,
  totalViews,
  onBack,
  onForward,
  onNavigate,
}: OnboardingModalContentProps) {
  const { t } = useTranslation();

  return (
    <div className="relative mx-auto flex h-[450px] flex-col  sm:h-[480px]">
      <div className="flex h-1/2 max-h-[264px] w-full grow self-center overflow-hidden rounded-t-xl bg-auto bg-center bg-no-repeat">
        <HeaderImage
          image={currentView.headerImage}
          hasWebp={currentView.hasWebp}
          isMainTitle={currentView.isMainTitle}
          isFirstView={isOnFirstView}
        />
      </div>
      <div className="flex flex-col justify-center overflow-y-auto rounded-b-xl px-8 pt-6 text-center">
        {currentView.renderContent(t)}
      </div>

      <NavigationDots
        totalViews={totalViews}
        currentIndex={currentViewIndex}
        onChange={onNavigate}
      />

      <div className="absolute left-1 top-1/2 -translate-y-1/2 sm:-left-16">
        {!isOnFirstView && (
          <Button
            icon={<ChevronLeft />}
            backgroundClasses="outline-2 sm:outline-0"
            onClick={onBack}
            type="secondary"
            dataTestId="back-button"
          />
        )}
      </div>
      <div className="absolute right-1 top-1/2 -translate-y-1/2 sm:-right-16">
        <Button
          icon={isOnLastView ? <Check /> : <ChevronRight />}
          backgroundClasses={`outline-2 sm:outline-0 ${
            isOnLastView && 'dark:bg-brand-green-dark'
          }`}
          onClick={onForward}
          type={isOnLastView ? 'primary' : 'secondary'}
          dataTestId={isOnLastView ? 'close-modal' : 'next-button'}
        />
      </div>
    </div>
  );
}

export function OnboardingModal() {
  const [hasOnboardingBeenSeen, setHasOnboardingBeenSeen] = useAtom(
    hasOnboardingBeenSeenAtom
  );
  const [searchParameters] = useSearchParams();
  const skipOnboarding = searchParameters.get('skip-onboarding') === 'true';
  const [isOpen, setIsOpen] = useState(!hasOnboardingBeenSeen && !skipOnboarding);
  const [currentViewIndex, setCurrentViewIndex] = useState(0);

  const handleDismiss = useCallback(() => {
    setHasOnboardingBeenSeen(true);
    setIsOpen(false);
  }, [setHasOnboardingBeenSeen]);

  const isConsumptionOnlyMode = useFeatureFlag('consumption-only');
  const onboardingViews = isConsumptionOnlyMode
    ? [...views.slice(0, TOGGLE_MODE_IDX), ...views.slice(TOGGLE_MODE_IDX + 1)]
    : views;

  const currentView = onboardingViews[currentViewIndex];
  const isOnLastView = currentViewIndex === onboardingViews.length - 1;
  const isOnFirstView = currentViewIndex === 0;

  const handleBack = () => {
    if (!isOnFirstView) {
      setCurrentViewIndex(currentViewIndex - 1);
    }
  };

  const handleForward = () => {
    if (isOnLastView) {
      handleDismiss();
    } else {
      setCurrentViewIndex(currentViewIndex + 1);
    }
  };

  const handleOpenStateChange = useCallback(
    (isOpen: boolean) => {
      if (!isOpen) {
        handleDismiss();
        setIsOpen(false);
      }
    },
    [handleDismiss]
  );
  return (
    <Modal
      isOpen={isOpen}
      setIsOpen={handleOpenStateChange}
      testId="onboarding"
      fullWidth
    >
      <OnboardingModalContent
        currentView={currentView}
        isOnFirstView={isOnFirstView}
        isOnLastView={isOnLastView}
        currentViewIndex={currentViewIndex}
        totalViews={onboardingViews.length}
        onBack={handleBack}
        onForward={handleForward}
        onNavigate={setCurrentViewIndex}
      />
    </Modal>
  );
}
