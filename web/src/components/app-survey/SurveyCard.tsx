import { useTranslation } from 'react-i18next';

import FeedbackCard, { SurveyResponseProps } from './FeedbackCard';

function postSurveyResponse({
  feedbackScore,
  inputText,
  reference: surveyReference,
}: SurveyResponseProps) {
  fetch(`https://hooks.zapier.com/hooks/catch/14671709/3l9daod/`, {
    method: 'POST',
    body: JSON.stringify({
      score: feedbackScore,
      feedback: inputText,
      reference: surveyReference,
    }),
  });
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
