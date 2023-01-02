import { ReactElement, useState } from 'react';

import { HiCheck, HiChevronLeft, HiChevronRight, HiXMark } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';

interface Page {
  headerImage: { pathname: string };
  isMainTitle?: boolean;
  renderContent: (translator: any) => ReactElement;
  title?: (translator: any) => ReactElement;
}

function Modal({
  modalName,
  views,
  visible,
  onDismiss,
}: {
  modalName: string;
  views: Page[];
  visible: boolean;
  onDismiss: () => void;
}) {
  const { __ } = useTranslation();
  const [currentViewIndex, setCurrentViewIndex] = useState(0);
  const isOnLastView = () => currentViewIndex === views.length - 1;
  const isOnFirstView = () => currentViewIndex === 0;

  const handleBack = () => {
    if (!isOnFirstView()) {
      setCurrentViewIndex(currentViewIndex - 1);
    }
  };
  const handleForward = () => {
    if (!isOnLastView()) {
      setCurrentViewIndex(currentViewIndex + 1);
    }
  };

  if (!visible) {
    return null;
  }
  const currentView = views[currentViewIndex];

  const RightButton = isOnLastView() ? (
    <button
      className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-green"
      onClick={onDismiss}
    >
      <HiCheck size="32" color="white" />
    </button>
  ) : (
    <button
      className="flex h-12 w-12 items-center justify-center rounded-full bg-white pl-1 dark:bg-gray-900"
      onClick={handleForward}
    >
      <HiChevronRight size="32" />
    </button>
  );

  return (
    <>
      <div
        className="absolute inset-0 z-40  bg-gray-800   bg-opacity-20"
        onClick={onDismiss}
        onKeyDown={onDismiss}
        role="presentation"
      />
      <div
        className="pointer-events-none  absolute top-auto z-50 flex w-full min-w-[500px]
       items-center justify-center self-center"
        data-test-id={modalName}
      >
        <div className="pointer-events-auto flex w-full max-w-[75px] flex-col justify-around">
          {!isOnFirstView() && (
            <button
              className="flex h-12 w-12 items-center justify-center rounded-full bg-white pr-1 dark:bg-gray-900"
              onClick={handleBack}
            >
              <HiChevronLeft size="32" />
            </button>
          )}
        </div>
        <div
          className={
            'color-white pointer-events-auto relative flex h-[500px] w-1/2 max-w-[700px] flex-col rounded-3xl bg-gray-50 shadow  dark:bg-gray-700'
          }
        >
          <div className="absolute self-end p-4 align-baseline">
            <button
              className="p-auto pointer-events-auto flex h-12 w-12 items-center justify-center rounded-full bg-white shadow dark:bg-gray-900"
              onClick={onDismiss}
            >
              <HiXMark size="28" />
            </button>
          </div>
          <div
            className={`flex h-1/2 max-h-[264px]
              w-full flex-grow rounded-t-xl bg-auto bg-center bg-no-repeat ${
                isOnFirstView() ? 'dark:invert' : ''
              }`}
            style={
              currentView.headerImage && {
                backgroundImage: `url("${currentView.headerImage.pathname}")`,
                backgroundSize: `${currentView.isMainTitle ? 'contain' : 'cover'} `,
              }
            }
          >
            <div>{currentView.title && <h1>{currentView.title(__)}</h1>}</div>
          </div>
          <div className="flex flex-col justify-center px-4 pt-6 text-center dark:bg-gray-700">
            {currentView.renderContent(__)}
          </div>
        </div>
        <div className="absolute bottom-[-60px] left-auto h-[40px] self-center  ">
          {views.map((view: Page, index: number) => (
            <div
              key={`modal-step-item-${index}`}
              className={`mx-2 inline-block h-[14px] w-[14px] rounded-xl bg-white ${
                index === currentViewIndex ? 'bg-brand-green' : ''
              }`}
            />
          ))}
        </div>
        <div className="pointer-events-auto flex w-full max-w-[75px] flex-col items-end  ">
          {RightButton}
        </div>
      </div>
    </>
  );
}

export default Modal;
