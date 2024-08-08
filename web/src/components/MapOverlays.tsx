import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtomValue } from 'jotai';
import { lazy, Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { hasSeenSurveyCardAtom } from 'utils/state/atoms';
import { useIsBiggerThanMobile } from 'utils/styling';

import SurveyCard from './app-survey/SurveyCard';
import LegendContainer from './legend/LegendContainer';

export default function MapOverlays() {
  const hasSeenSurveyCard = useAtomValue(hasSeenSurveyCardAtom);
  const isBiggerThanMobile = useIsBiggerThanMobile();

  const [searchParameters] = useSearchParams();
  const showManager =
    searchParameters.get('ff') === 'true' || searchParameters.get('ff') === '';
  const isProductionOrFManagerOpen = !import.meta.env.DEV || showManager;
  const surveyEnabled =
    useFeatureFlag('feedback-micro-survey') &&
    !hasSeenSurveyCard &&
    isProductionOrFManagerOpen;

  const FeatureFlagsManager = showManager
    ? lazy(() => import('features/feature-flags/FeatureFlagsManager'))
    : () => undefined;

  return (
    <div className="pointer-events-none fixed top-12 z-20 m-3 flex flex-col items-end space-y-3 sm:bottom-0 sm:right-0 sm:top-auto ">
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
      {surveyEnabled && (
        <Suspense>
          <SurveyCard />
        </Suspense>
      )}
    </div>
  );
}
