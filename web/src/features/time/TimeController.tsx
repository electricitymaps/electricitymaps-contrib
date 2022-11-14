import useGetState from 'api/getState';
import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state';

export default function TimeController() {
  const { __ } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetimeIndex, setSelectedDatetimeIndex] = useAtom(
    selectedDatetimeIndexAtom
  );
  const { data, isLoading, isError } = useGetState(timeAverage);

  if (isLoading || isError) {
    return <div>Loading...</div>;
  }

  const { datetimes } = data.data;

  const onTimeSliderChange = (datetimeIndex: number) => {
    // TODO: Does this work properly missing values?
    setSelectedDatetimeIndex(datetimes[datetimeIndex]);
  };

  return (
    <div
      className={
        'absolute bottom-20 left-3 right-3 rounded-xl bg-white p-5 shadow-md sm:max-w-md'
      }
    >
      <div className="flex flex-row items-center justify-between">
        <p className="mb-2 text-sm font-bold">{__('time-controller.title')}</p>
        <div className="mb-2 rounded-full bg-gray-100 py-2 px-3 text-xs">
          {selectedDatetimeIndex}
        </div>
      </div>
      <TimeAverageToggle className="mb-2" />
      <TimeSlider onChange={onTimeSliderChange} datetimes={datetimes} />
    </div>
  );
}
