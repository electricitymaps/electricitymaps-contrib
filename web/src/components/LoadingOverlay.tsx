import { animated, useTransition } from '@react-spring/web';
import useGetState from 'api/getState';
import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtomValue } from 'jotai';
import { useEffect, useState } from 'react';

import LoadingSpinner from './LoadingSpinner';

const TIME_BEFORE_SHOWING_RELOAD_BUTTON = 8000;

// TODO: Consider splitting up the icon and the overlay into two different components.
// That way we can maybe reuse it in panels for a loading indicator there.
// TODO: Consider loading svg directly or via img tag instead of the background-image
// approach used here.
function FadingOverlay({ isVisible }: { isVisible: boolean }) {
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
  }, [isVisible, showButton]);

  return transitions(
    (styles, isVisible) =>
      isVisible && (
        <animated.div
          className="fixed z-50 h-full w-full bg-gray-100 dark:bg-gray-900"
          style={styles}
          data-test-id="loading-overlay"
        >
          <LoadingSpinner showReloadButton={showButton} />
        </animated.div>
      )
  );
}

export default function LoadingOverlay() {
  const { isSuccess, isError } = useGetState();
  const isLoadingMap = useAtomValue(loadingMapAtom);
  const hasResult = isSuccess || isError;
  const showLoadingOverlay = !hasResult || isLoadingMap;
  return <FadingOverlay isVisible={showLoadingOverlay} />;
}
