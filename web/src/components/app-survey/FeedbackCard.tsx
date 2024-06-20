import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import Pill from 'components/Pill';
import { useAtom, useSetAtom } from 'jotai';
import {
  ChangeEvent,
  Dispatch,
  SetStateAction,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useTranslation } from 'react-i18next';
import { HiXMark } from 'react-icons/hi2';
import { hasSeenSurveyCardAtom, userLocationAtom } from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

enum FeedbackState {
  INITIAL = 'initial',
  OPTIONAL = 'optional',
  SUCCESS = 'success',
}

export interface SurveyResponseProps {
  feedbackScore: number;
  inputText: string;
  reference: string;
  location?: string;
}
interface FeedbackCardProps {
  postSurveyResponse: (props: SurveyResponseProps) => void;
  subtitle?: string;
  primaryQuestion: string;
  secondaryQuestionHigh?: string;
  secondaryQuestionLow?: string;
  surveyReference?: string;
}

export default function FeedbackCard({
  postSurveyResponse,
  subtitle,
  primaryQuestion,
  secondaryQuestionHigh,
  secondaryQuestionLow,
  surveyReference,
}: FeedbackCardProps) {
  const [isClosed, setIsClosed] = useState(false);
  const [feedbackState, setFeedbackState] = useState(FeedbackState.INITIAL);
  const setHasSeenSurveyCard = useSetAtom(hasSeenSurveyCardAtom);
  const isMobile = useIsMobile();

  const handleClose = () => {
    setIsClosed(true);
    if (surveyReference === 'Map Survey') {
      setHasSeenSurveyCard(true);
    }
  };
  const { t } = useTranslation();
  const title = t('feedback-card.title');
  const successMessage = t('feedback-card.success-message');
  const successSubtitle = t('feedback-card.success-subtitle');
  const isFeedbackSubmitted = feedbackState === FeedbackState.SUCCESS;

  const feedbackCardReference = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      const target = event.target as HTMLElement;
      if (
        feedbackCardReference.current &&
        !feedbackCardReference.current.contains(target) &&
        (isFeedbackSubmitted || isMobile)
      ) {
        setIsClosed(true);
        setHasSeenSurveyCard(true);
      }
    };

    if (!isClosed) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isClosed, isFeedbackSubmitted, isMobile, setHasSeenSurveyCard]);
  if (isClosed) {
    return null;
  }

  return (
    <div
      data-test-id="feedback-card"
      className="flex w-full flex-col gap-2 rounded-lg border border-neutral-200 bg-zinc-50 px-3 py-4 transition-all dark:border-gray-700 dark:bg-gray-900"
      ref={feedbackCardReference}
    >
      <div className="flex flex-row  justify-between">
        <div className="flex flex-initial flex-row gap-2">
          <div
            className={`min-h-[16px] min-w-[16px] bg-[url('/images/electricitymaps-icon.svg')] bg-contain bg-center bg-no-repeat dark:invert`}
          />
          <h2
            className={`self-center text-left text-sm font-semibold text-black dark:text-white`}
            data-test-id="title"
          >
            {isFeedbackSubmitted ? successSubtitle : title}
          </h2>
        </div>
        <button data-test-id="close-button" onClick={handleClose}>
          <HiXMark />
        </button>
      </div>
      <div>
        <div
          className={`pb-1 ${
            isFeedbackSubmitted ? 'text-sm' : 'text-xs'
          } font-medium text-neutral-400`}
          data-test-id="subtitle"
        >
          {isFeedbackSubmitted ? successMessage : subtitle}
        </div>
        <FeedbackActions
          feedbackState={feedbackState}
          setFeedbackState={setFeedbackState}
          postSurveyResponse={postSurveyResponse}
          surveyReference={surveyReference}
          primaryQuestion={primaryQuestion}
          inputQuestionHigh={secondaryQuestionHigh}
          inputQuestionLow={secondaryQuestionLow}
        />
      </div>
    </div>
  );
}

const calculateTextareaHeight = (event: ChangeEvent<HTMLTextAreaElement>) => {
  event.target.style.height = 'auto';
  event.target.style.height = event.target.scrollHeight + 2 + 'px';
};

function InputField({
  inputText,
  inputQuestion,
  handleInputChange,
}: {
  inputText: string;
  inputQuestion?: string;
  handleInputChange: (event: { target: { value: SetStateAction<string> } }) => void;
}) {
  const { t } = useTranslation();
  const inputPlaceholder = t('feedback-card.placeholder');
  const optional = t('feedback-card.optional');

  return (
    <div>
      <div className="flex flex-wrap justify-start">
        <span className="text-sm font-normal text-black dark:text-white">
          <span className="pr-1 font-semibold">{optional}</span>
          <span data-test-id="input-title">{inputQuestion}</span>
        </span>
      </div>
      <textarea
        data-test-id="feedback-input"
        value={inputText}
        onChange={(event) => {
          handleInputChange(event);
          calculateTextareaHeight(event);
        }}
        rows={1}
        placeholder={inputPlaceholder}
        className="my-2 w-full resize-none rounded border border-neutral-200 bg-transparent text-base focus:border-brand-green focus:ring-0 dark:border-gray-700"
      />
    </div>
  );
}

function SubmitButton({ handleSave }: { handleSave: () => void }) {
  const { t } = useTranslation();
  const buttonText = t('feedback-card.submit');

  return <Pill text={buttonText} onClick={handleSave} />;
}

function FeedbackActions({
  feedbackState,
  setFeedbackState,
  postSurveyResponse,
  inputQuestionHigh,
  inputQuestionLow,
  primaryQuestion,
  surveyReference,
}: {
  feedbackState: FeedbackState;
  setFeedbackState: Dispatch<SetStateAction<FeedbackState>>;
  postSurveyResponse: (props: SurveyResponseProps) => void;
  primaryQuestion: string;
  inputQuestionHigh?: string;
  inputQuestionLow?: string;
  surveyReference?: string;
}) {
  const [inputText, setInputText] = useState('');
  const [feedbackScore, setFeedbackScore] = useState('');
  const [userLocation] = useAtom(userLocationAtom);

  const handleInputChange = (event: { target: { value: SetStateAction<string> } }) => {
    setInputText(event.target.value);
  };

  const handleSave = () => {
    setFeedbackState(FeedbackState.SUCCESS);
    postSurveyResponse({
      feedbackScore: Number.parseInt(feedbackScore),
      inputText,
      reference: surveyReference ?? 'Unknown',
      location: userLocation,
    });
  };

  if (feedbackState === FeedbackState.SUCCESS) {
    return null;
  }

  return (
    <div className="flex flex-col">
      <div data-test-id="feedback-question" className="text-sm">
        {primaryQuestion}
      </div>
      <ActionPills
        setFeedbackState={setFeedbackState}
        setFeedbackScore={setFeedbackScore}
      />
      {feedbackState === FeedbackState.OPTIONAL && (
        <div>
          <div className="my-3 h-[1px] w-full bg-neutral-200 dark:bg-gray-700" />
          <div>
            <InputField
              inputText={inputText}
              handleInputChange={handleInputChange}
              inputQuestion={
                Number.parseInt(feedbackScore) > 3 ? inputQuestionHigh : inputQuestionLow
              }
            />
            <SubmitButton handleSave={handleSave} />
          </div>
        </div>
      )}
    </div>
  );
}

function ActionPills({
  setFeedbackState,
  setFeedbackScore,
}: {
  setFeedbackState: Dispatch<SetStateAction<FeedbackState>>;
  setFeedbackScore: Dispatch<SetStateAction<string>>;
}) {
  const { t } = useTranslation();
  const agreeText = t('feedback-card.agree');
  const [pillContent] = useState(['1', '2', '3', '4', '5']);
  const disagreeText = t('feedback-card.disagree');
  const [currentPillNumber, setPillNumber] = useState('');

  const handlePillClick = (identifier: string) => {
    setFeedbackScore(identifier);
    setPillNumber(identifier);
    setFeedbackState(FeedbackState.OPTIONAL);
  };

  return (
    <div className="flex w-full flex-col pt-2">
      <PillContent
        pillContent={pillContent}
        handlePillClick={handlePillClick}
        currentPillNumber={currentPillNumber}
      />
      <div className="flex flex-row items-center justify-between pt-1">
        <div
          data-test-id="disagree-text"
          className="text-xs font-medium text-neutral-400"
        >
          {disagreeText}
        </div>
        <div data-test-id="agree-text" className="text-xs font-medium text-neutral-400">
          {agreeText}
        </div>
      </div>
    </div>
  );
}

function PillContent({
  pillContent,
  handlePillClick,
  currentPillNumber,
}: {
  pillContent: string[];
  handlePillClick: (identifier: string) => void;
  currentPillNumber: string;
}) {
  return (
    <ToggleGroupPrimitive.Root
      className={'flex-start mb-2 flex flex-row items-center justify-between gap-3'}
      type="single"
    >
      {pillContent.map((content) => (
        <ToggleGroupPrimitive.Item
          data-test-id={`feedback-pill-${content}`}
          key={content}
          value={content}
          aria-label={content}
          onClick={() => handlePillClick(content)}
          className={`
          inline-flex h-9 w-full select-none items-center justify-center rounded-full border border-neutral-200 text-black  dark:border-gray-700 dark:text-white
            ${
              currentPillNumber == content
                ? 'bg-black dark:bg-white'
                : 'hover:bg-neutral-200 dark:hover:bg-gray-700'
            }`}
        >
          <div
            className={`text-sm font-semibold ${
              currentPillNumber == content ? ' text-zinc-50 dark:text-gray-900' : ''
            }`}
          >
            {content}
          </div>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}
