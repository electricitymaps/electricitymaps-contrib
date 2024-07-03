import useGetState from 'api/getState';
import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';
import { atom, useAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import trackEvent from 'utils/analytics';
import { TimeAverages } from 'utils/constants';
import { dateToDatetimeString } from 'utils/helpers';
import {
  availableDatetimesAtom,
  numberOfEntriesAtom,
  selectedDatetimeIndexAtom,
  selectedDatetimeStringAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

import TimeAxis from './TimeAxis';
import TimeHeader from './TimeHeader';

export default function TimeController({ className }: { className?: string }) {
  const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetimeIndex, setSelectedDatetimeIndex] = useAtom(
    selectedDatetimeIndexAtom
  );
  const [selectedDatetimeString, setSelectedDatetimeString] = useAtom(
    selectedDatetimeStringAtom
  );
  const [numberOfEntries, setNumberOfEntries] = useAtom(numberOfEntriesAtom);
  const [availableDatetimes, setAvailableDatetimes] = useAtom(availableDatetimesAtom);
  const { data, isLoading: dataLoading } = useGetState();

  // Show a loading state if isLoading is true or if there is only one datetime,
  // as this means we either have no data or only have latest hour loaded yet
  const isLoading = dataLoading || Object.keys(data?.data?.datetimes ?? {}).length === 1;

  // TODO: Figure out whether we want to work with datetimes as strings
  // or as Date objects. In this case datetimes are easier to work with
  const datetimes = useMemo(
    () => (data ? Object.keys(data.data?.datetimes).map((d) => new Date(d)) : undefined),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- is loading is used to trigger the re-memoization on hour change
    [data]
  );
  datetimes && setAvailableDatetimes(datetimes);

  const onToggleGroupClick = (timeAverage: TimeAverages) => {
    setTimeAverage(timeAverage);

    // Set time slider to latest value before switching aggregate to avoid flickering
    datetimes && setNumberOfEntries(datetimes.length - 1);
    datetimes && setSelectedDatetimeIndex(datetimes.length - 1);
    datetimes &&
      setSelectedDatetimeString(dateToDatetimeString(datetimes.at(-1) as Date));

    trackEvent('Time Aggregate Button Clicked', { timeAverage });
    console.log('Index', selectedDatetimeIndex);
    console.log('String', selectedDatetimeString);
  };

  return (
    <div className={className}>
      <TimeHeader
        // Hide the header on mobile as it is loaded directly into the BottomSheet header section
        className="hidden sm:flex"
      />
      <TimeAverageToggle
        timeAverage={timeAverage}
        onToggleGroupClick={onToggleGroupClick}
      />
      <TimeSlider />
      <TimeAxis
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        isLoading={isLoading}
        className="h-[22px] w-full overflow-visible"
        transform={`translate(12, 0)`}
        isLiveDisplay={timeAverage === TimeAverages.HOURLY}
      />
    </div>
  );
}
