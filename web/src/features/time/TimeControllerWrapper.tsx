import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtom } from 'jotai';
import { BottomSheet } from 'react-spring-bottom-sheet';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';
import TimeController from './TimeController';
import TimeHeader from './TimeHeader';

const SNAP_POINTS = [60, 160];

function BottomSheetWrappedTimeController() {
  const [isLoadingMap] = useAtom(loadingMapAtom);
  const [hasOnboardingBeenSeen] = useAtom(hasOnboardingBeenSeenAtom);

  // Don't show the time controller until the onboarding has been seen
  // But it still has to be rendered to avoid re-querying data and showing loading
  // indicators again. Therefore we set the snap points to 0 until modal is closed.
  const snapPoints = hasOnboardingBeenSeen ? SNAP_POINTS : [0];

  return (
    <BottomSheet
      scrollLocking={false} // Ensures scrolling is not blocked on IOS
      open={!isLoadingMap}
      snapPoints={() => snapPoints}
      blocking={false}
      header={<TimeHeader />}
    >
      <TimeController className="p-2 px-4 pt-1" />
    </BottomSheet>
  );
}

function FloatingTimeController() {
  return (
    <div className="fixed bottom-3 left-3 z-20 w-[calc(14vw_+_16rem)] rounded-xl bg-white p-5 shadow-md dark:bg-gray-900  md:w-[calc((14vw_+_16rem)_-_30px)]">
      <TimeController />
    </div>
  );
}

export default function TimeControllerWrapper() {
  const isBiggerThanMobile = useBreakpoint('sm');
  return isBiggerThanMobile ? (
    <FloatingTimeController />
  ) : (
    <BottomSheetWrappedTimeController />
  );
}
