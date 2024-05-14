import FeedbackCard from './FeedbackCard';

function postSurveyResponse() {
  console.log('Survey response posted');
}
export default function SurveyCard() {
  return (
    <div className="invisible  z-20  sm:visible ">
      <FeedbackCard
        surveyReference="Map Survey"
        postSurveyResponse={postSurveyResponse}
      />
    </div>
  );
}
