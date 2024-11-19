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
import { endDatetimeAtom, isHourlyAtom, startDatetimeAtom } from 'utils/state/atoms';

const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;

export default function HistoricalTimeHeader() {
  const { i18n } = useTranslation();
  const startDatetime = useAtomValue(startDatetimeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const { isLoading } = useGetState();
  const { urlDatetime } = useParams<RouteParameters>();
  const navigate = useNavigateWithParameters();

  const handleTimeNavigation = (direction: 'left' | 'right') => {
    if (!endDatetime || (!urlDatetime && direction === 'right')) {
      return;
    }

    const currentDate = urlDatetime ? new Date(urlDatetime) : new Date(endDatetime);
    const newDate = new Date(
      currentDate.getTime() +
        (direction === 'left' ? -TWENTY_FOUR_HOURS : TWENTY_FOUR_HOURS)
    );

    if (direction === 'right') {
      const twentyFourHoursAgo = new Date(Date.now() - TWENTY_FOUR_HOURS);
      if (newDate >= twentyFourHoursAgo) {
        navigate({ datetime: '' });
        return;
      }
    }

    navigate({ datetime: newDate.toISOString() });
  };

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
        <Button
          backgroundClasses="bg-transparent"
          onClick={() => handleTimeNavigation('left')}
          size="sm"
          type="tertiary"
          isDisabled={!isHourly}
          icon={
            <ChevronLeft
              className={twMerge('text-brand-green', !isHourly && 'opacity-50')}
            />
          }
        />
        <Button
          backgroundClasses="bg-transparent"
          size="sm"
          onClick={() => handleTimeNavigation('right')}
          type="tertiary"
          isDisabled={!isHourly || !urlDatetime}
          icon={
            <ChevronRight
              className={twMerge(
                'text-brand-green',
                (!urlDatetime || !isHourly) && 'opacity-50'
              )}
            />
          }
        />
        <Button
          size="sm"
          type="secondary"
          onClick={() => navigate({ datetime: '' })}
          isDisabled={!urlDatetime}
        >
          Latest
        </Button>
      </div>
    </div>
  );
}
