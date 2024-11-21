import Badge from 'components/Badge';
import { Button } from 'components/Button';
import { FormattedTime } from 'components/Time';
import { useAtomValue } from 'jotai';
import { ArrowRightToLine, ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import { TimeAverages } from 'utils/constants';
import { useNavigateWithParameters } from 'utils/helpers';
import {
  endDatetimeAtom,
  isHourlyAtom,
  startDatetimeAtom,
  useTimeAverageSync,
} from 'utils/state/atoms';

const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
const SEVENTY_TWO_HOURS = 72 * 60 * 60 * 1000;

const useHistoricalNavigation = () => {
  const isHourly = useAtomValue(isHourlyAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const { urlDatetime } = useParams<RouteParameters>();
  const navigate = useNavigateWithParameters();

  const offset = isHourly ? TWENTY_FOUR_HOURS : SEVENTY_TWO_HOURS;

  return {
    handleRightClick: () => {
      if (!endDatetime || !urlDatetime) {
        return;
      }
      const currentEndDatetime = new Date(endDatetime);
      const newDate = new Date(currentEndDatetime.getTime() + offset);

      const clampedDatetime = new Date(Date.now() - offset);
      if (newDate >= clampedDatetime) {
        navigate({ datetime: '' });
        return;
      }
      navigate({ datetime: newDate.toISOString() });
    },

    handleLeftClick: () => {
      if (!endDatetime) {
        return;
      }
      const currentEndDatetime = new Date(endDatetime);
      const newDate = new Date(currentEndDatetime.getTime() - offset);
      navigate({ datetime: newDate.toISOString() });
    },

    handleLatestClick: () => navigate({ datetime: '' }),
  };
};

const useIsHistorical = () => {
  const [selectedTimeAverage] = useTimeAverageSync();
  const isHistoricalTimeAverage = [TimeAverages.HOURLY, TimeAverages.HOURLY_72].includes(
    selectedTimeAverage
  );

  return isHistoricalTimeAverage;
};

export default function HistoricalTimeHeader() {
  const { i18n } = useTranslation();
  const startDatetime = useAtomValue(startDatetimeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const isHistoricalTimeAverage = useIsHistorical();
  const { urlDatetime } = useParams<RouteParameters>();

  const { handleRightClick, handleLeftClick, handleLatestClick } =
    useHistoricalNavigation();

  return (
    <div className="flex min-h-6 flex-row items-center justify-between">
      {startDatetime && endDatetime && (
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
      {isHistoricalTimeAverage && (
        <div className="flex h-6 flex-row items-center gap-x-3">
          <Button
            backgroundClasses="bg-transparent"
            onClick={handleLeftClick}
            size="sm"
            type="tertiary"
            icon={
              <ChevronLeft
                size={22}
                className={twMerge(
                  'text-brand-green',
                  !isHistoricalTimeAverage && 'opacity-50'
                )}
              />
            }
          />
          <Button
            backgroundClasses="bg-transparent"
            size="sm"
            onClick={handleRightClick}
            type="tertiary"
            isDisabled={!urlDatetime}
            icon={
              <ChevronRight
                className={twMerge(
                  'text-brand-green',
                  (!urlDatetime || !isHistoricalTimeAverage) && 'opacity-50'
                )}
                size={22}
              />
            }
          />
          <Button
            size="sm"
            type="tertiary"
            onClick={handleLatestClick}
            isDisabled={!urlDatetime}
            icon={
              <ArrowRightToLine
                className={twMerge(
                  'text-brand-green',
                  (!urlDatetime || !isHistoricalTimeAverage) && 'opacity-50'
                )}
                size={22}
              />
            }
          />
        </div>
      )}
    </div>
  );
}
