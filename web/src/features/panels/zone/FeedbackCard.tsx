import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import Pill from 'components/Pill';
import { Dispatch, SetStateAction, useEffect, useState } from 'react';
import { HiOutlineX } from 'react-icons/hi';
import { useTranslation } from 'translation/translation';

export default function FeedbackCard() {
  const [isClosed, setIsClosed] = useState(false);
  const [state, setState] = useState('1');

  const handleClose = () => {
    setIsClosed(true);
  };

  const title = getQuestionTranslation('title', state);
  const subtitle = getQuestionTranslation('subtitle', state);

  if (isClosed) {
    return null; // Don't render the component if closed
  }

  return (
    <div
      data-test-id="feedback-card"
      className="mb-4 flex w-full flex-col rounded-lg border border-neutral-200 bg-zinc-50 pl-2.5 transition-all dark:border-gray-700 dark:bg-gray-900"
    >
      <div className="flex flex-row items-center justify-between">
        <div className="flex flex-initial flex-row gap-2">
          <div
            className={`h-[16px] w-[16px] bg-[url('/images/emaps-icon-light.svg')] bg-contain bg-center dark:bg-[url('/images/emaps-icon-dark.svg')]`}
          />
          <h2
            className={`self-center text-left text-sm font-semibold text-black dark:text-white`}
            data-test-id="title"
          >
            {title}
          </h2>
        </div>
        <button data-test-id="close-button" onClick={handleClose} className="px-3 py-2.5">
          <HiOutlineX />
        </button>
      </div>
      <div className="pb-2 pr-2.5">
        <div
          className="pb-1 text-xs font-medium text-neutral-400"
          data-test-id="subtitle"
        >
          {subtitle}
        </div>
        <FeedbackActions state={state} setState={setState} />
      </div>
    </div>
  );
}

function InputField({
  inputText,
  handleInputChange,
}: {
  inputText: string;
  handleInputChange: (event: { target: { value: SetStateAction<string> } }) => void;
}) {
  const inputPlaceholder = getQuestionTranslation('placeholder');
  const optional = getQuestionTranslation('optional');
  const text = getQuestionTranslation('input-question');

  return (
    <div>
      <div className="flex justify-start">
        <div className="pr-1 text-sm font-semibold text-black dark:text-white">
          {optional}
        </div>
        <div
          data-test-id="input-title"
          className="text-sm font-normal text-black dark:text-white"
        >
          {text}
        </div>
      </div>
      <input
        data-test-id="feedback-input"
        value={inputText}
        onChange={handleInputChange}
        placeholder={inputPlaceholder}
        className="my-2 h-11 w-full items-center rounded border border-neutral-200 bg-transparent p-3 pl-2 text-base focus:outline-brand-green dark:border-gray-700"
      />
    </div>
  );
}

function SubmitButton({ handleSave }: { handleSave: () => void }) {
  const buttonText = getQuestionTranslation('submit');

  return (
    <Pill
      classes="dark:hover:bg-gray-700 disabled:dark:text-gray-700 disabled:text-neutral-200 dark:text-white text-black hover:bg-neutral-200 border border-black dark:border-white disabled:dark:border-gray-700 disabled:border-neutral-200 h-9 w-full"
      text={buttonText}
      isButton={true}
      onClick={handleSave}
    />
  );
}

function FeedbackActions({
  state,
  setState,
}: {
  state: string;
  setState: Dispatch<SetStateAction<string>>;
}) {
  const [inputText, setInputText] = useState('');

  const question = getQuestionTranslation('rate-question');

  const handleInputChange = (event: { target: { value: SetStateAction<string> } }) => {
    setInputText(event.target.value);
  };

  const handleSave = () => {
    setState('3');
  };

  if (state === '3') {
    return null;
  }

  return (
    <div className="flex flex-col">
      <div data-test-id="feedback-question" className="text-sm">
        {question}
      </div>
      <ActionPills setState={setState} />
      {state === '2' && (
        <div>
          <div className="my-3 h-[1px] w-full bg-neutral-200 dark:bg-gray-700" />
          <div>
            <InputField inputText={inputText} handleInputChange={handleInputChange} />
            <SubmitButton handleSave={handleSave} />
          </div>
        </div>
      )}
    </div>
  );
}

function ActionPills({ setState }: { setState: Dispatch<SetStateAction<string>> }) {
  const agreeText = getQuestionTranslation('agree');
  const [pillContent] = useState([1, 2, 3, 4, 5]);
  const disagreeText = getQuestionTranslation('disagree');
  const [CurrentPillNumber, setPillNumber] = useState('');

  useEffect(() => {}, [CurrentPillNumber]);

  const handlePillClick = (identifier: string) => {
    setPillNumber(identifier);
    setState('2');
  };

  return (
    <div className="flex w-full max-w-sm flex-col pt-2">
      <PillContent
        pillContent={pillContent}
        handlePillClick={handlePillClick}
        CurrentPillNumber={CurrentPillNumber}
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
  CurrentPillNumber,
}: {
  pillContent: number[];
  handlePillClick: (identifier: string) => void;
  CurrentPillNumber: string;
}) {
  return (
    <ToggleGroupPrimitive.Root
      className={'flex-start mb-2 flex flex-row items-center justify-between'}
      type="multiple"
      aria-label="Font settings"
    >
      {pillContent.map((content) => (
        <ToggleGroupPrimitive.Item
          data-test-id={`feedback-pill-${content}`}
          key={content}
          value={String(content)}
          aria-label={String(content)}
          onClick={() => handlePillClick(String(content))}
          className={`
          mr-2 inline-flex h-9 w-[60px] select-none items-center justify-center rounded-full border border-neutral-200 text-black  dark:border-gray-700 dark:text-white
            ${
              CurrentPillNumber == String(content)
                ? 'bg-black dark:bg-white'
                : 'hover:bg-neutral-200 dark:hover:bg-gray-700'
            }`}
        >
          <div
            className={`text-xs font-semibold ${
              CurrentPillNumber == String(content)
                ? ' text-zinc-50 dark:text-gray-900'
                : ''
            }`}
          >
            {content}
          </div>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}

function getQuestionTranslation(field: string, state?: string) {
  const { __ } = useTranslation();
  if (state !== undefined) {
    if (state == '2') {
      return __(`estimation-feedback.${field}.state-1`);
    }
    return __(`estimation-feedback.${field}.state-${state}`);
  }
  return __(`estimation-feedback.${field}`);
}
