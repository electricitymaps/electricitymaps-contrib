import { useFeatureFlag } from 'features/feature-flags/api';
import FeatureFlagsManager from 'features/feature-flags/FeatureFlagsManager';
import { useAtomValue } from 'jotai';
import { Suspense } from 'react';
import { hasSeenSurveyCardAtom } from 'utils/state/atoms';

import SurveyCard from './app-survey/SurveyCard';
import LegendContainer from './legend/LegendContainer';

export default function MapOverlays() {
  const hasSeenSurveyCard = useAtomValue(hasSeenSurveyCardAtom);
  const surveyEnabled = useFeatureFlag('feedback-micro-survey') && !hasSeenSurveyCard;

  return (
    <div className="pointer-events-none fixed top-12 z-20 m-3 flex flex-col items-end space-y-3 sm:bottom-0 sm:right-0 sm:top-auto">
      <Suspense>
        <div className="hidden sm:flex">
          <FeatureFlagsManager />
        </div>
      </Suspense>
      <Suspense>
        <div className="hidden sm:flex">
          <LegendContainer />
        </div>
      </Suspense>
      {surveyEnabled && (
        <Suspense>
          <SurveyCard />
        </Suspense>
      )}
    </div>
  );
}
