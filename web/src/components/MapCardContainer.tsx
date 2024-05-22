import { useFeatureFlag } from 'features/feature-flags/api';
import FeatureFlagsManager from 'features/feature-flags/FeatureFlagsManager';
import { useAtomValue } from 'jotai';
import { Suspense } from 'react';
import { hasSeenSurveyPopupAtom } from 'utils/state/atoms';

import SurveyCard from './app-survey/SurveyCard';
import LegendContainer from './legend/LegendContainer';

export default function MapCardContainer() {
  const hasSeenSurveyPopup = useAtomValue(hasSeenSurveyPopupAtom);
  const surveyEnabled = useFeatureFlag('feedback-micro-survey') && !hasSeenSurveyPopup;

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
