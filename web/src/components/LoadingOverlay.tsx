import { animated, useTransition } from '@react-spring/web';
import useGetState from 'api/getState';
import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtom } from 'jotai';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from './Button';

const TIME_BEFORE_SHOWING_RELOAD_BUTTON = 8000;

// TODO: Consider splitting up the icon and the overlay into two different components.
// That way we can maybe reuse it in panels for a loading indicator there.
// TODO: Consider loading svg directly or via img tag instead of the background-image
// approach used here.
function FadingOverlay({ isVisible }: { isVisible: boolean }) {
  const { t } = useTranslation();

  const [showButton, setShowButton] = useState(false);
  const transitions = useTransition(isVisible, {
    from: { opacity: 1 },
    leave: { opacity: 0 },
  });

  // Show the reload button after some time
  // Show the reload button after some time
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (showButton === false && isVisible) {
        setShowButton(true);
      }
    }, TIME_BEFORE_SHOWING_RELOAD_BUTTON);
    return () => {
      clearTimeout(timeoutId);
      setShowButton(false);
    };
  }, [isVisible]);

  return transitions(
    (styles, isVisible) =>
      isVisible && (
        <animated.div
          className="fixed z-50 h-full w-full bg-gray-100 dark:bg-gray-900"
          style={styles}
          data-test-id="loading-overlay"
        >
          <div className="flex h-full flex-col items-center justify-center">
            <div className="h-40 w-40 bg-[url('/images/loading-icon.svg')] bg-[length:100px] bg-center bg-no-repeat dark:bg-gray-900 dark:bg-[url('/images/loading-icon-darkmode.svg')]" />
            {showButton && (
              <>
                <p>{t('misc.slow-loading-text')}</p>
                <Button
                  className="w-20 min-w-min dark:bg-gray-800/80"
                  aria-label="Reload page"
                  onClick={() => window.location.reload()}
                >
                  {t('misc.reload')}
                </Button>
              </>
            )}
          </div>
        </animated.div>
      )
  );
}

export default function LoadingOverlay() {
  const { isLoading, isError } = useGetState();
  const [isLoadingMap] = useAtom(loadingMapAtom);

  const showLoadingOverlay = !isError && (isLoading || isLoadingMap);

  return <FadingOverlay isVisible={showLoadingOverlay} />;
}
