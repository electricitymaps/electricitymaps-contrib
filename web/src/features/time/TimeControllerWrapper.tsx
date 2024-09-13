import { loadingMapAtom } from 'features/map/mapAtoms';
import { useDarkMode } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useMemo, useRef } from 'react';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import { ReactBottomSheet } from './ReactBottomSheet';
import TimeController from './TimeController';
import TimeHeader from './TimeHeader';

function ReactBottomSheetWrappedTimeController() {
  const isDarkModeEnabled = useDarkMode();
  const [isLoadingMap] = useAtom(loadingMapAtom);
  const [hasOnboardingBeenSeen] = useAtom(hasOnboardingBeenSeenAtom);
  const safeAreaBottomString = getComputedStyle(
    document.documentElement
  ).getPropertyValue('--sab');

  const safeAreaBottom = safeAreaBottomString
    ? Number.parseInt(safeAreaBottomString.replace('px', ''))
    : 0;
  const SNAP_POINTS = [60 + safeAreaBottom, 160 + safeAreaBottom];

  const snapPoints = hasOnboardingBeenSeen && !isLoadingMap ? SNAP_POINTS : [0, 0];
  const ExcludedElementReference = useRef<HTMLDivElement>(null);

  const memoizedContent = useMemo(
    () => (
      <div className="rounded-t-2xl bg-white px-4 pt-2 shadow-2xl dark:bg-gray-800">
        <div className="mb-2 flex justify-center">
          <div className="h-[3px] w-9 rounded-full bg-gray-300"></div>
        </div>
        <TimeHeader />
        <TimeController
          ref={ExcludedElementReference}
          className="min-[370px] pb-2 pt-1"
        />
      </div>
    ),
    []
  );

  return (
    <ReactBottomSheet
      excludeElementRef={ExcludedElementReference}
      backgroundColor={isDarkModeEnabled ? 'rgb(31, 41, 55)' : 'white'}
      snapPoints={snapPoints}
    >
      {memoizedContent}
    </ReactBottomSheet>
  );
}

function FloatingTimeController() {
  return (
    <div className="fixed bottom-3 left-3 z-20 w-[calc(14vw_+_16rem)] rounded-xl bg-white px-4 py-3 shadow-xl drop-shadow-2xl dark:bg-gray-800 min-[780px]:w-[calc((14vw_+_16rem)_-_30px)] xl:px-5">
      <TimeController />
    </div>
  );
}

export default function TimeControllerWrapper() {
  const isBiggerThanMobile = useBreakpoint('sm');
  return isBiggerThanMobile ? (
    <FloatingTimeController />
  ) : (
    <ReactBottomSheetWrappedTimeController />
  );
}
