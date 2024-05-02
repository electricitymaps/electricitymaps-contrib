import FeatureFlagsManager from 'features/feature-flags/FeatureFlagsManager';
import { Suspense } from 'react';

import SurveyCard from './app-survey/SurveyCard';
import LegendContainer from './legend/LegendContainer';

export default function MapCardContainer() {
  return (
    <div className="fixed bottom-4 right-4 z-20 flex-col space-y-3">
      <Suspense>
        <FeatureFlagsManager />
      </Suspense>
      <Suspense>
        <LegendContainer />
      </Suspense>
      <Suspense>
        <SurveyCard />
      </Suspense>
    </div>
  );
}
