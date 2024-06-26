import { TFunction } from 'i18next';
import { ReactElement, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiCheck, HiChevronLeft, HiChevronRight, HiXMark } from 'react-icons/hi2';

export interface Page {
  headerImage: { pathname: string };
  isMainTitle?: boolean;
  renderContent: (translator: TFunction) => ReactElement;
  title?: (translator: TFunction) => ReactElement;
  hasWebp?: boolean;
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
  const { t } = useTranslation();
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
      className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-green shadow"
      data-test-id="close-modal"
      onClick={onDismiss}
    >
      <HiCheck size="24" color="white" />
    </button>
  ) : (
    <button
      className="flex h-10 w-10 items-center justify-center rounded-full bg-white pl-1 shadow dark:bg-gray-900"
      onClick={handleForward}
    >
      <HiChevronRight size="24" />
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
        className="px-auto pointer-events-none  absolute top-auto z-50 mx-auto flex w-full items-center justify-center
       self-center sm:top-20 sm:min-w-[500px]"
        data-test-id={modalName}
      >
        <div className="pointer-events-auto z-10 flex w-full max-w-[35px] shrink flex-col justify-around px-2 sm:max-w-[60px]">
          {!isOnFirstView() && (
            <button
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white pr-1 shadow dark:bg-gray-900"
              onClick={handleBack}
            >
              <HiChevronLeft size="24" />
            </button>
          )}
        </div>
        <div className="color-white pointer-events-auto relative flex h-[450px] w-auto max-w-[500px] flex-col rounded-3xl bg-gray-50 shadow-lg sm:h-[500px]  dark:bg-gray-700">
          <div className="absolute self-end p-4 align-baseline">
            <button
              className="p-auto pointer-events-auto flex h-10 w-10 items-center justify-center rounded-full bg-white shadow dark:bg-gray-900"
              onClick={onDismiss}
              data-test-id="close-modal"
            >
              <HiXMark size="28" />
            </button>
          </div>
          <div
            className={`flex h-1/2 max-h-[264px] w-full grow self-center
              rounded-t-3xl bg-auto bg-center bg-no-repeat ${
                isOnFirstView() ? 'max-w-[10rem] dark:invert' : ''
              }`}
            style={
              currentView.headerImage && !currentView.hasWebp
                ? {
                    backgroundImage: `url("${currentView.headerImage.pathname}")`,
                    backgroundSize: `${currentView.isMainTitle ? 'contain' : 'cover'} `,
                  }
                : {}
            }
          >
            {currentView.headerImage && currentView.hasWebp && (
              <picture className="overflow-hidden" style={{}}>
                <source
                  srcSet={`${currentView.headerImage.pathname}.webp`}
                  type="image/webp"
                />
                <img
                  src={`${currentView.headerImage.pathname}.png`}
                  alt=""
                  className="w-full rounded-t-3xl object-top"
                  draggable={false}
                />
              </picture>
            )}
            <h1>{currentView.title?.(t)}</h1>
          </div>
          <div className="flex w-auto flex-col justify-center px-4 pt-6 text-center dark:bg-gray-700">
            {currentView.renderContent(t)}
          </div>
        </div>
        <div className="pointer-events-auto absolute bottom-[-60px] left-auto  h-[40px] self-center">
          {views.map((view: Page, index: number) => (
            <button
              key={`modal-step-item-${index}`}
              className={` mx-2 inline-block h-[14px] w-[14px] rounded-xl ${
                index === currentViewIndex ? 'bg-brand-green' : 'bg-white'
              }`}
              onClick={() => setCurrentViewIndex(index)}
            />
          ))}
        </div>
        <div className="pointer-events-auto z-10 flex w-full max-w-[35px] flex-col items-end px-2 sm:max-w-[60px]">
          {RightButton}
        </div>
      </div>
    </>
  );
}

export default Modal;
