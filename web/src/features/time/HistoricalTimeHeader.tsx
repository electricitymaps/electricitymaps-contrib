import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { Button } from 'components/Button';
import { FormattedTime } from 'components/Time';
import { useAtomValue } from 'jotai';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import { useNavigateWithParameters } from 'utils/helpers';
import { endDatetimeAtom, startDatetimeAtom } from 'utils/state/atoms';

function setToMidnightUTC(date: Date): Date {
  const newDate = new Date(date);
  newDate.setUTCHours(0, 0, 0, 0);
  return newDate;
}
function formatDateToISO(date: Date): string {
  return date.toISOString().slice(0, -5) + 'Z';
}

export default function TimeHeader() {
  const { i18n } = useTranslation();
  const startDatetime = useAtomValue(startDatetimeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const { isLoading } = useGetState();
  const { urlDatetime } = useParams<RouteParameters>();
  const navigate = useNavigateWithParameters();
  function handleLeftClick() {
    if (!urlDatetime && !endDatetime) {
      return;
    }

    const targetDate = urlDatetime ? new Date(urlDatetime) : endDatetime;
    if (!targetDate) {
      return;
    }

    const midnightDate = setToMidnightUTC(targetDate);
    const newDate = new Date(midnightDate);
    urlDatetime
      ? newDate.setUTCDate(midnightDate.getUTCDate() - 1)
      : newDate.setUTCDate(midnightDate.getUTCDate());

    navigate({ datetime: formatDateToISO(newDate) });
  }

  function handleRightClick() {
    if (!endDatetime) {
      return;
    }

    const midnightDate = setToMidnightUTC(new Date(endDatetime));
    const newDate = new Date(midnightDate);
    newDate.setUTCDate(midnightDate.getUTCDate() + 1);

    const now = new Date();
    const twentyFourHoursAgo = setToMidnightUTC(now);
    twentyFourHoursAgo.setUTCDate(twentyFourHoursAgo.getUTCDate() - 1);

    if (newDate >= twentyFourHoursAgo) {
      navigate({ datetime: '' });
      return;
    }

    navigate({ datetime: formatDateToISO(newDate) });
  }
  return (
    <div className="flex min-h-6 flex-row items-center justify-between">
      {!isLoading && startDatetime && endDatetime && (
        <Badge
          pillText={
            <FormattedTime
              datetime={startDatetime}
              language={i18n.languages[0]}
              endDatetime={endDatetime}
            />
          }
          type="success"
        />
      )}
      <div className="flex flex-row items-center gap-2">
        <ChevronLeft onClick={handleLeftClick} className="text-brand-green" />
        <ChevronRight
          onClick={handleRightClick}
          className={twMerge('text-brand-green', !urlDatetime && 'opacity-50')}
        />
        <Button
          size="sm"
          type="secondary"
          onClick={() => {
            navigate({ datetime: '' });
          }}
          isDisabled={!urlDatetime}
        >
          Latest
        </Button>
      </div>
    </div>
  );
}
