import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtom } from 'jotai';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import TimeController from './TimeController';

function FloatingTimeController() {
  return (
    <div className="fixed bottom-3 left-3 z-20 w-[calc(14vw_+_16rem)] rounded-xl bg-white px-4 py-3 shadow-xl drop-shadow-2xl min-[780px]:w-[calc((14vw_+_16rem)_-_30px)] xl:px-5  dark:bg-gray-800">
      <TimeController />
    </div>
  );
}

function FixedTimeController() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 w-full bg-white px-4 py-3 shadow-xl drop-shadow-2xl dark:bg-gray-800">
      <TimeController />
    </div>
  );
}

export default function TimeControllerWrapper() {
  const isBiggerThanMobile = useBreakpoint('sm');
  return isBiggerThanMobile ? <FloatingTimeController /> : <FixedTimeController />;
}
