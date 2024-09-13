import useGetState from 'api/getState';
import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';
import { useAtom, useAtomValue } from 'jotai';
import { forwardRef, useCallback, useEffect, useMemo, useState } from 'react';
import { twMerge } from 'tailwind-merge';
import trackEvent from 'utils/analytics';
import { TimeAverages } from 'utils/constants';
import {
  isHourlyAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { useIsBiggerThanMobile } from 'utils/styling';

import TimeAxis from './TimeAxis';
import TimeHeader from './TimeHeader';

const TimeController = forwardRef<HTMLDivElement, { className?: string }>(
  ({ className }, reference) => {
    const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
    const isHourly = useAtomValue(isHourlyAtom);
    const [selectedDatetime, setSelectedDatetime] = useAtom(selectedDatetimeIndexAtom);
    const [numberOfEntries, setNumberOfEntries] = useState(0);
    const { data, isLoading: dataLoading } = useGetState();
    const isBiggerThanMobile = useIsBiggerThanMobile();

    // Show a loading state if isLoading is true or if there is only one datetime,
    // as this means we either have no data or only have latest hour loaded yet
    const isLoading =
      dataLoading || Object.keys(data?.data?.datetimes ?? {}).length === 1;

    // TODO: Figure out whether we want to work with datetimes as strings
    // or as Date objects. In this case datetimes are easier to work with
    const datetimes = useMemo(
      () =>
        data ? Object.keys(data.data?.datetimes).map((d) => new Date(d)) : undefined,
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
        setSelectedDatetime({
          datetime: selectedDatetime.datetime,
          index: numberOfEntries,
        });
        setTimeAverage(timeAverage);
        trackEvent('Time Aggregate Button Clicked', { timeAverage });
      },
      [selectedDatetime.datetime, numberOfEntries, setSelectedDatetime, setTimeAverage]
    );

    return (
      <div ref={reference} className={twMerge(className, 'flex flex-col gap-3')}>
        {isBiggerThanMobile && <TimeHeader />}
        <TimeAverageToggle
          timeAverage={timeAverage}
          onToggleGroupClick={onToggleGroupClick}
        />
        <div>
          {/* The above div is needed to treat the TimeSlider and TimeAxis as one DOM element */}
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
          />
        </div>
      </div>
    );
  }
);

TimeController.displayName = 'TimeController';
export default TimeController;
