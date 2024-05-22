import { useFeatureFlag } from 'features/feature-flags/api';
import FeatureFlagsManager from 'features/feature-flags/FeatureFlagsManager';
import { useAtomValue } from 'jotai';
import { Suspense } from 'react';
import { hasSeenSurveyCardAtom } from 'utils/state/atoms';

import SurveyCard from './app-survey/SurveyCard';
import LegendContainer from './legend/LegendContainer';

export default function MapCardContainer() {
  const hasSeenSurveyCard = useAtomValue(hasSeenSurveyCardAtom);
  const surveyEnabled = useFeatureFlag('feedback-micro-survey') && !hasSeenSurveyCard;

  return (
    <div className="fixed bottom-4 right-4 z-20 flex flex-col items-end space-y-3">
      <Suspense>
        <FeatureFlagsManager />
      </Suspense>
      <Suspense>
        <LegendContainer />
      </Suspense>
      {surveyEnabled && (
        <Suspense>
          <SurveyCard />
        </Suspense>
      )}
    </div>
  );
}
