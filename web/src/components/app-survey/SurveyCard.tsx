import { useTranslation } from 'react-i18next';

import FeedbackCard, { SurveyResponseProps } from './FeedbackCard';

async function postSurveyResponse({
  feedbackScore,
  inputText,
  reference: surveyReference,
  location = 'Unknown',
}: SurveyResponseProps) {
  try {
    const response = await fetch(
      `https://hooks.zapier.com/hooks/catch/14671709/3vzj7zn/`,
      {
        method: 'POST',
        body: JSON.stringify({
          score: feedbackScore,
          feedback: inputText,
          reference: surveyReference,
          location,
        }),
      }
    );

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const result = await response.json();
    if (result.result === 'success') {
      console.debug('Feedback submitted successfully.');
    } else {
      console.error('Error submitting feedback:', result);
    }
  } catch (error) {
    console.error('Error submitting user feedback:', error);
  }
}

export default function SurveyCard() {
  const { t } = useTranslation();
  return (
    <div className="pointer-events-auto z-20 sm:max-w-96">
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
