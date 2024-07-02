import { TFunction } from 'i18next';
import { ReactElement, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiCheck, HiChevronLeft, HiChevronRight, HiXMark } from 'react-icons/hi2';
import { useMediaQuery } from 'utils';

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
  const isMinHeight = useMediaQuery('(min-height: 675px)');
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
        <div
          className={`color-white pointer-events-auto relative flex w-auto rounded-3xl bg-gray-50 shadow-lg ${
            isMinHeight
              ? 'h-[450px] max-w-[500px] flex-col sm:h-[500px]'
              : 'h-[250px] w-full max-w-[1000px] flex-row sm:h-[250px]'
          } dark:bg-gray-700`}
        >
          <div
            className={`absolute ${
              isMinHeight ? 'self-end' : 'right-0 self-baseline'
            } p-4 align-baseline`}
          >
            <button
              className="p-auto pointer-events-auto flex h-10 w-10 items-center justify-center rounded-full bg-white shadow dark:bg-gray-900"
              onClick={onDismiss}
              data-test-id="close-modal"
            >
              <HiXMark size="28" />
            </button>
          </div>
          <div
            className={`flex w-full grow self-center
              ${
                isMinHeight ? 'h-1/2 max-h-[264px] rounded-t-3xl' : 'h-full rounded-l-3xl'
              } bg-auto bg-center bg-no-repeat ${
              isOnFirstView()
                ? 'max-w-[10rem] dark:invert'
                : (isMinHeight
                ? ''
                : 'max-w-[400px]')
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
                  className={`${
                    isMinHeight
                      ? 'w-full rounded-t-3xl object-top'
                      : 'h-full rounded-l-3xl object-contain object-right'
                  }`}
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
