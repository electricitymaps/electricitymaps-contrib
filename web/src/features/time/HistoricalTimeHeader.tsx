import { Button } from 'components/Button';
import {
  NewFeaturePopover,
  POPOVER_ID,
} from 'components/NewFeaturePopover/NewFeaturePopover';
import { NewFeaturePopoverContent } from 'components/NewFeaturePopover/NewFeaturePopoverContent';
import { FormattedTime } from 'components/Time';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtomValue } from 'jotai';
import { ArrowRightToLine, ChevronLeft, ChevronRight } from 'lucide-react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import trackEvent from 'utils/analytics';
import { MAX_HISTORICAL_LOOKBACK_DAYS, TimeRange, TrackEvent } from 'utils/constants';
import { useNavigateWithParameters } from 'utils/helpers';
import {
  endDatetimeAtom,
  isHourlyAtom,
  startDatetimeAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

const TIME_OFFSETS: Partial<Record<TimeRange, number>> = {
  [TimeRange.H24]: 24,
  [TimeRange.H72]: 72,
};

const clamp = (date: number, offset: number) => {
  const clampAt = Date.now() - Math.abs(offset);
  const newDate = date + offset;
  if (newDate > clampAt) {
    return '';
  }

  return new Date(newDate).toISOString();
};

const EMPTY_IMPLEMENTATION = {
  handleRightClick() {},
  handleLeftClick() {},
  handleLatestClick() {},
  isWithinHistoricalLimit: true,
};

const useHistoricalNavigation = () => {
  const timeRange = useAtomValue(timeRangeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const { urlDatetime } = useParams<RouteParameters>();
  const navigate = useNavigateWithParameters();

  const offset = (TIME_OFFSETS[timeRange] || 0) * 60 * 60 * 1000;

  return useMemo(() => {
    if (!endDatetime || !offset) {
      return EMPTY_IMPLEMENTATION;
    }

    let isWithinHistoricalLimit = true;

    if (urlDatetime) {
      const targetDate = new Date(urlDatetime);
      targetDate.setUTCHours(targetDate.getUTCHours() - (TIME_OFFSETS[timeRange] || 0));

      const maxHistoricalDate = new Date();
      maxHistoricalDate.setUTCDate(
        maxHistoricalDate.getUTCDate() - MAX_HISTORICAL_LOOKBACK_DAYS
      );

      isWithinHistoricalLimit = targetDate >= maxHistoricalDate;
    }

    return {
      handleRightClick() {
        trackEvent(TrackEvent.HISTORICAL_NAVIGATION, {
          direction: 'forward',
        });
        navigate({ datetime: clamp(endDatetime.getTime(), offset) });
      },
      handleLeftClick() {
        trackEvent(TrackEvent.HISTORICAL_NAVIGATION, {
          direction: 'backward',
        });
        navigate({ datetime: clamp(endDatetime.getTime(), -offset) });
      },
      handleLatestClick() {
        trackEvent(TrackEvent.HISTORICAL_NAVIGATION, {
          direction: 'latest',
        });
        navigate({ datetime: '' });
      },
      isWithinHistoricalLimit,
    };
  }, [offset, endDatetime, navigate, urlDatetime, timeRange]);
};

export default function HistoricalTimeHeader() {
  const { i18n } = useTranslation();
  const startDatetime = useAtomValue(startDatetimeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const { urlDatetime } = useParams<RouteParameters>();
  const isNewFeaturePopoverEnabled = useFeatureFlag(POPOVER_ID);

  const {
    isWithinHistoricalLimit,
    handleRightClick,
    handleLeftClick,
    handleLatestClick,
  } = useHistoricalNavigation();

  if (!isHourly && startDatetime && endDatetime) {
    return (
      <div className="flex min-h-6 flex-row items-center justify-center">
        <FormattedTime
          datetime={startDatetime}
          language={i18n.languages[0]}
          endDatetime={endDatetime}
          className="text-sm font-semibold"
        />
      </div>
    );
  }

  return (
    <div className="relative flex h-6 w-full items-center">
      <div className="absolute flex w-full items-center justify-between px-10">
        <Button
          backgroundClasses="bg-transparent"
          onClick={handleLeftClick}
          size="sm"
          type="tertiary"
          isDisabled={!isWithinHistoricalLimit}
          icon={
            <ChevronLeft
              size={22}
              className={twMerge(
                'text-brand-green dark:text-success-dark',
                !isWithinHistoricalLimit && 'opacity-50'
              )}
            />
          }
        />
        {startDatetime && endDatetime && (
          <FormattedTime
            datetime={startDatetime}
            language={i18n.languages[0]}
            endDatetime={endDatetime}
            className="text-sm font-semibold"
          />
        )}
        <Button
          backgroundClasses="bg-transparent"
          size="sm"
          onClick={handleRightClick}
          type="tertiary"
          isDisabled={!urlDatetime}
          icon={
            <ChevronRight
              className={twMerge(
                'text-brand-green dark:text-success-dark',
                !urlDatetime && 'opacity-50'
              )}
              size={22}
            />
          }
        />
      </div>
      <Button
        backgroundClasses="absolute z-1 right-2"
        size="sm"
        type="tertiary"
        onClick={handleLatestClick}
        isDisabled={!urlDatetime}
        icon={
          <ArrowRightToLine
            className={twMerge(
              'text-brand-green dark:text-success-dark',
              !urlDatetime && 'opacity-50'
            )}
            size={22}
          />
        }
      />
    </div>
  );
}
