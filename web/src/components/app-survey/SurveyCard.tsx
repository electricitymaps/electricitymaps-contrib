import { useFeatureFlag } from 'features/feature-flags/api';

export default function SurveyCard() {
  const surveyEnabled = useFeatureFlag('feedback-micro-survey');
  if (!surveyEnabled) {
    return null;
  }
  return (
    <div className="invisible  z-20 flex w-[224px] flex-col rounded bg-white/90 px-1 py-2 shadow-xl backdrop-blur-sm sm:visible dark:bg-gray-800">
      this is a survey card
    </div>
  );
}
