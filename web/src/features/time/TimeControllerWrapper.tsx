import { useBreakpoint } from 'utils/styling';

import TimeController from './TimeController';

function FloatingTimeController() {
  return (
    <div className="fixed bottom-3 left-3 z-20 w-[calc(14vw_+_16rem)] rounded-xl bg-white/80 px-4 py-3 shadow-xl drop-shadow-2xl backdrop-blur min-[780px]:w-[calc((14vw_+_16rem)_-_30px)] xl:px-5 dark:bg-gray-800/80">
      <TimeController />
    </div>
  );
}

function FixedTimeController() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 w-full border-t border-neutral-200 bg-white/80 px-4 py-3 backdrop-blur dark:border-gray-700 dark:bg-gray-800/80">
      <TimeController />
    </div>
  );
}

export default function TimeControllerWrapper() {
  const isBiggerThanMobile = useBreakpoint('sm');
  return isBiggerThanMobile ? <FloatingTimeController /> : <FixedTimeController />;
}
