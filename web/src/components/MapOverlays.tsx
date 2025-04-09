import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtomValue } from 'jotai';
import { lazy, Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import {
  hasSeenSurveyCardAtom,
  hasSeenUsSurveyCardAtom,
  userLocationAtom,
} from 'utils/state/atoms';
import { useIsBiggerThanMobile } from 'utils/styling';

import SurveyCard from './app-survey/SurveyCard';
import LegendContainer from './legend/LegendContainer';

export default function MapOverlays() {
  const hasSeenSurveyCard = useAtomValue(hasSeenSurveyCardAtom);
  const hasSeenUsSurveyCard = useAtomValue(hasSeenUsSurveyCardAtom);
  const userLocation = useAtomValue(userLocationAtom);
  const isBiggerThanMobile = useIsBiggerThanMobile();
  const [searchParameters] = useSearchParams();
  const showManager =
    searchParameters.get('ff') === 'true' || searchParameters.get('ff') === '';
  const isProductionOrFManagerOpen = !import.meta.env.DEV || showManager;
  const isSurveyEnabled =
    useFeatureFlag('feedback-micro-survey') &&
    !hasSeenSurveyCard &&
    isProductionOrFManagerOpen;
  const isUsSurveyEnabled =
    useFeatureFlag('feedback-us-micro-survey') &&
    !hasSeenUsSurveyCard &&
    isProductionOrFManagerOpen &&
    userLocation?.startsWith('US');
  const FeatureFlagsManager = showManager
    ? lazy(() => import('features/feature-flags/FeatureFlagsManager'))
    : () => undefined;
  const isIntercomEnabled = useFeatureFlag('intercom-messenger');
  return (
    <div
      className={twMerge(
        'pointer-events-none fixed top-12 z-10 m-3 flex flex-col items-end space-y-3 sm:bottom-0 sm:right-0 sm:top-auto',
        isIntercomEnabled ? 'pr-20' : ''
      )}
    >
      {isBiggerThanMobile && (
        <>
          {showManager && (
            <Suspense>
              <FeatureFlagsManager />
            </Suspense>
          )}
          <Suspense>
            <LegendContainer />
          </Suspense>
        </>
      )}
      {(isSurveyEnabled || isUsSurveyEnabled) && (
        <Suspense>
          <SurveyCard isUsSurvey={isUsSurveyEnabled} />
        </Suspense>
      )}
    </div>
  );
}
