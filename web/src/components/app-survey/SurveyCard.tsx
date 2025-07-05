import { useTranslation } from 'react-i18next';

import FeedbackCard, { SurveyResponseProps } from './FeedbackCard';

const GENERAL_SURVEY_HOOK_URL = 'https://hooks.zapier.com/hooks/catch/14671709/3vzj7zn/';
const US_SURVEY_HOOK_URL = 'https://hooks.zapier.com/hooks/catch/14671709/2413b46/';

async function postSurveyResponse({
  feedbackScore,
  inputText,
  reference: surveyReference,
  location = 'Unknown',
  version,
  featureFlags,
  preceedingInputText: userJourneyText,
}: SurveyResponseProps) {
  try {
    const response = await fetch(
      surveyReference == 'US Survey' ? US_SURVEY_HOOK_URL : GENERAL_SURVEY_HOOK_URL,
      {
        method: 'POST',
        body: JSON.stringify({
          score: feedbackScore,
          feedback: inputText,
          reference: surveyReference,
          location,
          version,
          featureFlags: JSON.stringify(featureFlags)?.slice(1, -1),
          userJourney: userJourneyText,
          device: navigator.userAgent,
        }),
      }
    );

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const result = await response.json();
    if (result.status === 'success') {
      console.debug('Feedback submitted successfully.');
    } else {
      console.error('Error submitting feedback:', result);
    }
  } catch (error) {
    console.error('Error submitting user feedback:', error);
  }
}

export default function SurveyCard({ isUsSurvey }: { isUsSurvey?: boolean }) {
  const { t } = useTranslation();

  return (
    <div className="pointer-events-auto z-20 sm:max-w-96">
      {isUsSurvey ? (
        <FeedbackCard
          surveyReference={'US Survey'}
          postSurveyResponse={postSurveyResponse}
          primaryQuestion={'How satisfied are you with the US information in our app?'}
          secondaryQuestionHigh={
            'What changes would make our app more informative to people living in the US?'
          }
          secondaryQuestionLow={
            'What changes would make our app more informative to people living in the US?'
          }
          preceedingQuestion={'Where did you first hear about our app?'}
        />
      ) : (
        <FeedbackCard
          surveyReference={'Map Survey'}
          postSurveyResponse={postSurveyResponse}
          primaryQuestion={t(($) => $['feedback-card']['primary-question'])}
          secondaryQuestionHigh={t(($) => $['feedback-card']['secondary-question-high'])}
          secondaryQuestionLow={t(($) => $['feedback-card']['secondary-question-low'])}
        />
      )}
    </div>
  );
}
