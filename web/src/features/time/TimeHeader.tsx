import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { FormattedTime } from 'components/Time';
import { useAtomValue } from 'jotai';
import { ChevronLeft } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigateWithParameters } from 'utils/helpers';
import {
  endDatetimeAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

export default function TimeHeader() {
  const { t, i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();
  const navigate = useNavigateWithParameters();
  const endDatetime = useAtomValue(endDatetimeAtom);
  function handleLeftClick() {
    if (!endDatetime) {
      return;
    }
    const date = new Date(endDatetime);
    date.setUTCHours(date.getUTCHours() - 24);
    const newDateString = date.toISOString().slice(0, -5) + 'Z';
    navigate({ datetime: newDateString });
  }

  return (
    <div className="flex min-h-6 flex-row items-center">
      <h3 className="grow select-none text-left">
        {t(`time-controller.title.${timeAverage}`)}
      </h3>
      {!isLoading && (
        <>
          <ChevronLeft onClick={handleLeftClick} className="text-brand-green" />
          <Badge
            pillText={
              <FormattedTime
                datetime={selectedDatetime.datetime}
                language={i18n.languages[0]}
                timeAverage={timeAverage}
              />
            }
            type="success"
          />
        </>
      )}
    </div>
  );
}
