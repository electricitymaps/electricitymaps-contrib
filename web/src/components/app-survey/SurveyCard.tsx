import { useTranslation } from 'react-i18next';

import FeedbackCard from './FeedbackCard';

function postSurveyResponse() {
  console.log('Survey response posted');
}
export default function SurveyCard() {
  const { t } = useTranslation();
  return (
    <div className="invisible  z-20  sm:visible ">
      <FeedbackCard
        surveyReference="Map Survey"
        postSurveyResponse={postSurveyResponse}
        primaryQuestion={t('feedback-card.primary-question')}
        secondaryQuestionHigh={t('feedback-card.secondary-question-high')}
        secondaryQuestionLow={t('feedback-card.secondary-question-low')}
      />
    </div>
  );
}
