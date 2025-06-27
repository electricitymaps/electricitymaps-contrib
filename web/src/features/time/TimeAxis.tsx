import { Group } from '@visx/group';
import { ScaleTime, scaleTime } from 'd3-scale';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import PulseLoader from 'react-spinners/PulseLoader';
import useResizeObserver from 'use-resize-observer/polyfilled';
import { HOURLY_TIME_INDEX, TimeRange } from 'utils/constants';
import { getLocalTime, isValidHistoricalTimeRange } from 'utils/helpers';

import { formatDateTick } from '../../utils/formatting';

// The following represents a list of methods, indexed by time range, that depict
// if a datetime should be a major tick, where we will display the date value.

const getMajorTick = (
  timeRange: TimeRange,
  localHours: number,
  localMinutes: number,
  index: number
) => {
  switch (timeRange) {
    case TimeRange.H24: {
      return localHours % 4 === 0 && localMinutes === 0;
    }
    case TimeRange.H72: {
      return localHours === 12 || localHours === 0;
    }
    case TimeRange.M3:
    case TimeRange.ALL_MONTHS: {
      return index % 12 === 0;
    }
    case TimeRange.M12:
    case TimeRange.ALL_YEARS: {
      return true;
    }
    default: {
      return false;
    }
  }
};

const renderTick = (
  scale: ScaleTime<number, number, never>,
  value: Date,
  index: number,
  displayLive: boolean,
  lang: string,
  selectedTimeRange: TimeRange,
  isLoading: boolean,
  timezone?: string,
  chartHeight?: number,
  isTimeController?: boolean
) => {
  const { localHours, localMinutes } = getLocalTime(value, timezone);
  const isMidnightTime = localHours === 0;

  const isMajorTick =
    !isLoading && getMajorTick(selectedTimeRange, localHours, localMinutes, index);
  const isLastTick = index === HOURLY_TIME_INDEX[selectedTimeRange];
  const scaledValue = scale(value);
  const overlapsWithLive = scaledValue + 40 >= scale.range()[1]; // the "LIVE" labels takes ~30px
  const shouldShowValue = displayLive
    ? (isMajorTick && !overlapsWithLive) || isLastTick
    : isMajorTick;

  return (
    <Group key={index} className="text-xs" left={scaledValue}>
      {isMidnightTime &&
        isValidHistoricalTimeRange(selectedTimeRange) &&
        !isTimeController && (
          <line
            stroke="currentColor"
            strokeDasharray="2,2"
            y1={chartHeight ? -chartHeight : '-100%'}
            y2="0"
            opacity={0.6}
            className="midnight-marker"
          />
        )}
      <line stroke="currentColor" y2="6" opacity={isMajorTick ? 0.5 : 0.2} />
      {shouldShowValue &&
        renderTickValue(value, index, displayLive, lang, selectedTimeRange, timezone)}
    </Group>
  );
};

const renderTickValue = (
  v: Date,
  index: number,
  displayLive: boolean,
  lang: string,
  selectedTimeRange: TimeRange,
  timezone?: string
) => {
  const shouldDisplayLive = displayLive && index === HOURLY_TIME_INDEX[selectedTimeRange];
  const dateText = formatDateTick(v, lang, selectedTimeRange, timezone);
  const textOffset =
    isValidHistoricalTimeRange(selectedTimeRange) && dateText && dateText.length > 5
      ? 5
      : 0;

  return shouldDisplayLive ? (
    <g>
      <text fill="#DE3054" y="9" dy="0.71em" fontWeight="bold" textAnchor="middle">
        Live
      </text>
    </g>
  ) : (
    <text fill="currentColor" y="9" x={textOffset} dy="0.71em" fontSize={'0.65rem'}>
      {dateText}
    </text>
  );
};

const getTimeScale = (rangeEnd: number, startDate: Date, endDate: Date) =>
  scaleTime().domain([startDate, endDate]).range([0, rangeEnd]);
interface TimeAxisProps {
  selectedTimeRange: TimeRange;
  datetimes: Date[] | undefined;
  isLoading: boolean;
  scale?: ScaleTime<number, number>;
  isLiveDisplay?: boolean;
  transform?: string;
  scaleWidth?: number;
  className?: string;
  timezone?: string;
  chartHeight?: number;
  isTimeController?: boolean;
}

function TimeAxis({
  selectedTimeRange,
  datetimes,
  isLoading,
  transform,
  scaleWidth,
  isLiveDisplay,
  className,
  timezone,
  chartHeight,
  isTimeController,
}: TimeAxisProps) {
  const { i18n } = useTranslation();
  const { ref, width: observerWidth = 0 } = useResizeObserver<SVGSVGElement>();

  const width = observerWidth - 24;

  if (datetimes === undefined || isLoading) {
    return (
      <div className="flex h-[22px]  w-full justify-center">
        <PulseLoader size={6} color={'#135836'} />
      </div>
    );
  }

  const scale = getTimeScale(scaleWidth ?? width, datetimes[0], datetimes.at(-1) as Date);
  const [x1, x2] = scale.range();

  return (
    <svg className={className} ref={ref}>
      <g
        fill="none"
        textAnchor="middle"
        transform={transform}
        style={{ pointerEvents: 'none' }}
      >
        <path
          stroke={isTimeController ? 'none' : 'currentColor'}
          d={`M${x1},0H${x2}V0`}
          strokeWidth={0.5}
        />
        {datetimes.map((v, index) =>
          index < datetimes.length - 1 || isTimeController
            ? renderTick(
                scale,
                v,
                index,
                isLiveDisplay ?? false,
                i18n.language,
                selectedTimeRange,
                isLoading,
                timezone,
                chartHeight,
                isTimeController
              )
            : null
        )}
      </g>
    </svg>
  );
}

export default memo(TimeAxis);
