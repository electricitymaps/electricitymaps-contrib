import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtom } from 'jotai';
import { BottomSheet } from 'react-spring-bottom-sheet';
import { useBreakpoint } from 'utils/styling';
import TimeController from './TimeController';
import TimeHeader from './TimeHeader';

// These snap points should leave enough "safe area" at the bottom
const SNAP_POINTS = [80, 200];

function BottomSheetWrappedTimeController() {
  const [isLoadingMap] = useAtom(loadingMapAtom);

  return (
    <BottomSheet
      scrollLocking={false} // Ensures scrolling is not blocked on IOS
      open={!isLoadingMap}
      snapPoints={() => SNAP_POINTS}
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
  const isMinSM = useBreakpoint('sm');
  return isMinSM ? <FloatingTimeController /> : <BottomSheetWrappedTimeController />;
}
