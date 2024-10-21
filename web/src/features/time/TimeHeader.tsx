import useGetState from 'api/getState';
import { useAtom, useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export default function TimeHeader() {
  const { t, i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const [selectedDatetime, setSelectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  // TODO: Left and right arrows to change the date
  return (
    <div className="flex min-h-6 flex-row items-center">
      <h3 className="grow select-none text-left">
        {t(`time-controller.title.${timeAverage}`)}
      </h3>
      {!isLoading && (
        <input
          className="rounded-full border-none bg-success/10 py-1 pl-2 text-xs font-semibold text-success dark:bg-success-dark/10 dark:text-success-dark"
          type="date" // use month or year
          value={selectedDatetime.datetime.toISOString().slice(0, 10)}
          onChange={(event) => {
            trackEvent(TrackEvent.DATE_PICKER_CLICKED);
            setSelectedDatetime({ datetime: new Date(event.target.value), index: 0 });
          }}
          aria-label="Select date"
        ></input>
      )}
    </div>
  );
}
