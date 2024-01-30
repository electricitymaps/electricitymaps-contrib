import Pill from 'components/Pill';
import { SetStateAction, useState } from 'react';
import { HiOutlineX } from 'react-icons/hi';
import { useTranslation } from 'translation/translation';

export default function FeedbackCard() {
  const [isClosed, setIsClosed] = useState(false);
  const [state, setState] = useState('1');

  const handleClose = () => {
    setIsClosed(true);
  };

  const title = getQuestionTranslation(state, 'title');
  const subtitle = getQuestionTranslation(state, 'subtitle');
  const question = getQuestionTranslation(state, 'text');

  if (isClosed) {
    return null; // Don't render the component if closed
  }

  return (
    <div className="mb-4 flex w-full flex-col rounded-lg border border-neutral-200 bg-zinc-50 pl-2.5 transition-all dark:border-gray-700 dark:bg-gray-900">
      <div className="flex flex-row items-center justify-between">
        <div className="flex flex-initial flex-row gap-2">
          <div
            className={`h-[16px] w-[16px] bg-[url('/images/emaps-icon-light.svg')] bg-contain bg-center dark:bg-[url('/images/emaps-icon-dark.svg')]`}
          />
          <h2
            className={`self-center text-left text-sm font-semibold text-black dark:text-white`}
          >
            {title}
          </h2>
        </div>
        <button onClick={handleClose} className="px-3 py-2.5">
          <HiOutlineX />
        </button>
      </div>
      <div className="pb-2 pr-2.5">
        <div className="pb-1 text-xs font-medium text-neutral-400">{subtitle}</div>
        <div className="text-sm">{question}</div>
        <FeedbackActions state={state} setState={setState} />
      </div>
    </div>
  );
}

export function FeedbackActions({
  state,
  setState,
}: {
  state: string;
  setState: (state: string) => void;
}) {
  const [pillContent] = useState([1, 2, 3, 4, 5]);
  const agreeText = getQuestionTranslation(state, 'agree');
  const disagreeText = getQuestionTranslation(state, 'agree');
  const buttonText = getQuestionTranslation('2', 'button-text');
  const inputPlaceholder = getQuestionTranslation('2', 'input-text');

  const handlePillClick = (identifier: string) => {
    if (identifier === '1' || identifier === '2') {
      setState('3');
    } else if (identifier >= '3' && identifier <= '5') {
      setState('2');
    }
  };

  const [inputText, setInputText] = useState('');

  const handleInputChange = (event: { target: { value: SetStateAction<string> } }) => {
    setInputText(event.target.value);
  };

  const handleSave = () => {
    setState('3');
    console.log('Input text:', inputText);
  };

  const isDisabled = !inputText.trim();

  if (state === '1') {
    return (
      <div className="flex flex-col pt-2">
        <div className="flex flex-row">
          {pillContent.map((content) => (
            <Pill
              key={content}
              classes="dark:hover:bg-gray-700 hover:bg-neutral-200 border border-neutral-200 dark:border-gray-700 w-[60px] h-9 mr-2"
              text={String(content)}
              textColor="dark:text-white text-black"
              isButton={true}
              identifier={String(content)}
              onClick={handlePillClick}
            />
          ))}
        </div>
        <div className="flex flex-row items-center justify-between pt-1">
          <div className="text-xs font-medium text-neutral-400">{agreeText}</div>
          <div className="text-xs font-medium text-neutral-400">{disagreeText}</div>
        </div>
      </div>
    );
  } else if (state === '2') {
    return (
      <div>
        <input
          value={inputText}
          onChange={handleInputChange}
          placeholder={inputPlaceholder}
          // I can't get rid of the blue outline... heeelp
          className="my-2 h-11 w-full items-center rounded border border-neutral-200 bg-transparent p-3 pl-2 text-base focus:outline-none dark:border-gray-700"
        />
        <Pill
          classes="dark:hover:bg-gray-700 hover:bg-neutral-200 border border-black dark:border-white disabled:dark:border-gray-700 disabled:border-neutral-200 h-9 w-full"
          text={buttonText}
          textColor={
            isDisabled
              ? 'dark:text-gray-700 text-neutral-200'
              : 'dark:text-white text-black'
          }
          isButton={true}
          onClick={handleSave}
          isDisabled={isDisabled}
        />
      </div>
    );
  }
}

function getQuestionTranslation(state: string, field: string) {
  const { __ } = useTranslation();
  return __(`estimation-feedback.state-${state}.${field}`);
}
