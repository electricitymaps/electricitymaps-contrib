import useGetState from 'api/getState';
import Accordion from 'components/Accordion';
import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';
import { useAtom, useAtomValue } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TimeAverages } from 'utils/constants';
import {
  isHourlyAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { useIsBiggerThanMobile, useIsMobile } from 'utils/styling';

import TimeAxis from './TimeAxis';
import TimeBadge from './TimeBadge';

const timeControllerCollapsedAtom = atomWithStorage<boolean | null>(
  'timeControllerCollapsed',
  null
);

function InternalTimeController({ className }: { className?: string }) {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const [timeControllerCollapsed, setTimeControllerCollapsed] = useAtom(
    timeControllerCollapsedAtom
  );
  const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const [selectedDatetime, setSelectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [numberOfEntries, setNumberOfEntries] = useState(0);
  const { data, isLoading: dataLoading } = useGetState();

  // Show a loading state if isLoading is true or if there is only one datetime,
  // as this means we either have no data or only have latest hour loaded yet
  const isLoading = dataLoading || Object.keys(data?.data?.datetimes ?? {}).length === 1;

  // TODO: Figure out whether we want to work with datetimes as strings
  // or as Date objects. In this case datetimes are easier to work with
  const datetimes = useMemo(
    () => (data ? Object.keys(data.data?.datetimes).map((d) => new Date(d)) : undefined),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- is loading is used to trigger the re-memoization on hour change
    [data, isLoading]
  );

  useEffect(() => {
    if (datetimes) {
      // This value is stored in state to avoid flickering when switching between time averages
      // as this effect means index will be one render behind if using datetimes directly
      setNumberOfEntries(datetimes.length - 1);
      // Reset the selected datetime when data changes
      setSelectedDatetime({
        datetime: datetimes.at(-1) as Date,
        index: datetimes.length - 1,
      });
    }
  }, [data, datetimes, setSelectedDatetime]);

  const onTimeSliderChange = useCallback(
    (index: number) => {
      // TODO: Does this work properly missing values?
      if (!datetimes) {
        return;
      }
      setSelectedDatetime({
        datetime: datetimes[index],
        index,
      });
    },
    [datetimes, setSelectedDatetime]
  );

  const onToggleGroupClick = useCallback(
    (timeAverage: TimeAverages) => {
      // Set time slider to latest value before switching aggregate to avoid flickering
      setSelectedDatetime({
        datetime: selectedDatetime.datetime,
        index: numberOfEntries,
      });
      setTimeAverage(timeAverage);
      trackEvent('Time Aggregate Button Clicked', { timeAverage });
    },
    [selectedDatetime.datetime, numberOfEntries, setSelectedDatetime, setTimeAverage]
  );

  if (timeControllerCollapsed === null) {
    setTimeControllerCollapsed(isMobile);
  }

  return (
    <div className={className}>
      <Accordion
        title={t(`time-controller.title.${timeAverage}`)}
        badge={<TimeBadge />}
        isOnTop
        isCollapsedAtom={timeControllerCollapsedAtom}
      >
        <TimeAverageToggle
          timeAverage={timeAverage}
          onToggleGroupClick={onToggleGroupClick}
        />
      </Accordion>
      <TimeSlider
        onChange={onTimeSliderChange}
        numberOfEntries={numberOfEntries}
        selectedIndex={selectedDatetime.index}
      />
      <TimeAxis
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        isLoading={isLoading}
        className="h-[22px] w-full overflow-visible"
        transform={`translate(12, 0)`}
        isLiveDisplay={isHourly}
        isGraph={false}
      />
    </div>
  );
}

function FloatingTimeController() {
  return (
    <div className="fixed bottom-3 left-3 z-20 w-[calc(14vw_+_16rem)] rounded-2xl bg-white/80 px-4 py-3 shadow-xl drop-shadow-2xl backdrop-blur min-[780px]:w-[calc((14vw_+_16rem)_-_30px)] xl:px-5 dark:bg-gray-800/80">
      <InternalTimeController />
    </div>
  );
}

function FixedTimeController() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 w-full border-t border-neutral-200 bg-white/80 px-4 py-3 backdrop-blur dark:border-gray-700 dark:bg-gray-800/80">
      <InternalTimeController />
    </div>
  );
}

export default function TimeController() {
  const isBiggerThanMobile = useIsBiggerThanMobile();
  return isBiggerThanMobile ? <FloatingTimeController /> : <FixedTimeController />;
}
