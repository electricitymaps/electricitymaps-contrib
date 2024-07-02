import useGetState from 'api/getState';
import Accordion from 'components/Accordion';
import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';
import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TimeAverages } from 'utils/constants';
import { dateToDatetimeString } from 'utils/helpers';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

import TimeAxis from './TimeAxis';
import TimeHeader from './TimeBadge';

const timeControllerCollapsedAtom = atomWithStorage<boolean | null>(
  'timeControllerCollapsed',
  null
);

export default function TimeController({ className }: { className?: string }) {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
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
        datetimeString: dateToDatetimeString(datetimes.at(-1) as Date),
        index: datetimes.length - 1,
      });
    }
  }, [data, datetimes, setSelectedDatetime]);

  const onTimeSliderChange = (index: number) => {
    // TODO: Does this work properly missing values?
    if (!datetimes) {
      return;
    }
    setSelectedDatetime({
      datetimeString: dateToDatetimeString(datetimes[index]),
      index,
    });
  };

  const onToggleGroupClick = (timeAverage: TimeAverages) => {
    // Set time slider to latest value before switching aggregate to avoid flickering
    setSelectedDatetime({
      datetimeString: selectedDatetime.datetimeString,
      index: numberOfEntries,
    });
    setTimeAverage(timeAverage);
    trackEvent('Time Aggregate Button Clicked', { timeAverage });
  };

  return (
    <div className={className}>
      <Accordion
        title={t('time-controller.title')}
        badge={<TimeHeader />}
        isOnTop
        isCollapsedDefault={isMobile}
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
        isLiveDisplay={timeAverage === TimeAverages.HOURLY}
      />
    </div>
  );
}
