import useGetState from 'api/getState';
import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';
import { useAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import { useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import { dateToDatetimeIndex } from 'utils/helpers';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state';
import TimeAxis from './TimeAxis';

export default function TimeController() {
  const { __ } = useTranslation();
  const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime, setSelectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const { data, isLoading } = useGetState(timeAverage);

  useEffect(() => {
    if (datetimes) {
      // Reset the selected datetime when data changes
      setSelectedDatetime(dateToDatetimeIndex(datetimes[0]));
    }
  }, [data]);

  // TODO: Figure out whether we want to work with datetimes as strings
  // or as Date objects. In this case datetimes are easier to work with
  const datetimes = useMemo(
    () => (data ? data.data?.datetimes.map((d) => new Date(d)) : undefined),
    [data]
  );

  const onTimeSliderChange = (datetimeIndex: number) => {
    // TODO: Does this work properly missing values?
    if (!datetimes) {
      return;
    }
    setSelectedDatetime(dateToDatetimeIndex(datetimes[datetimeIndex]));
  };

  const onToggleGroupClick = (timeAverage: TimeAverages) => {
    setTimeAverage(timeAverage);
  };

  return (
    <div
      className={
        'md: absolute bottom-0 w-full rounded-t-xl bg-white p-5 shadow-md dark:bg-gray-900 md:bottom-3 md:left-3 md:max-w-md md:rounded-xl'
      }
    >
      <div className=" flex flex-row items-center justify-between">
        <p className="mb-2 text-base font-bold">{__('time-controller.title')}</p>
        <div className="mb-2 rounded-full bg-green-900/10 py-2 px-3 text-xs text-green-900 dark:bg-gray-700 dark:text-white">
          {!isLoading && formatDate(new Date(selectedDatetime), 'en', timeAverage)}
        </div>
      </div>
      <TimeAverageToggle
        timeAverage={timeAverage}
        onToggleGroupClick={onToggleGroupClick}
      />
      <TimeSlider
        onChange={onTimeSliderChange}
        numberOfEntries={datetimes?.length || 0}
        selectedIndex={datetimes?.findIndex(
          (d) => dateToDatetimeIndex(d) === selectedDatetime
        )}
      />
      <TimeAxis
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        isLoading={isLoading}
      />
    </div>
  );
}
