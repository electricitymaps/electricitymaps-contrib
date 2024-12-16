import { ScaleTime, scaleTime } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import PulseLoader from 'react-spinners/PulseLoader';
import useResizeObserver from 'use-resize-observer/polyfilled';
import { HOURLY_TIME_INDEX, TimeRange } from 'utils/constants';
import { isValidHistoricalTimeRange } from 'utils/helpers';

import { formatDateTick } from '../../utils/formatting';

// Frequency at which values are displayed for a tick
const TIME_TO_TICK_FREQUENCY = {
  '24h': 6,
  '72h': 12,
  '30d': 6,
  '12mo': 1,
  all: 1,
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
  // Special-casing index 72 for 72 hour resolution: Typically we retrieve resolution + 1 records
  // from app-backend, but we're retrieving only 72 records for 72 hour resolution

  const isMidnightTime = isMidnight(value, timezone);

  const shouldShowValue =
    !isLoading &&
    ((index % TIME_TO_TICK_FREQUENCY[selectedTimeRange] === 0 && index !== 72) ||
      index === HOURLY_TIME_INDEX[selectedTimeRange]);

  return (
    <g
      id={index.toString()}
      key={`timeaxis-tick-${index}`}
      className="text-xs"
      opacity={1}
      transform={`translate(${scale(value)},0)`}
    >
      {isMidnightTime && !isTimeController && (
        <line
          stroke="currentColor"
          strokeDasharray="2,2"
          y1={chartHeight ? -chartHeight : '-100%'}
          y2="0"
          opacity={0.6}
          className="midnight-marker"
        />
      )}
      <line stroke="currentColor" y2="6" opacity={shouldShowValue ? 0.5 : 0.2} />
      {shouldShowValue &&
        renderTickValue(value, index, displayLive, lang, selectedTimeRange, timezone)}
    </g>
  );
};

const isMidnight = (date: Date, timezone?: string) => {
  if (!timezone) {
    return date.getHours() === 0 && date.getMinutes() === 0;
  }

  const localDate = new Date(date.toLocaleString(undefined, { timeZone: timezone }));
  return localDate.getHours() === 0 && localDate.getMinutes() === 0;
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
      <circle cx="-1em" cy="1.15em" r="2" fill="red" />
      <text fill="#DE3054" y="9" x="5" dy="0.71em" fontWeight="bold" textAnchor="middle">
        LIVE
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
        <path stroke="none" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
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

export default TimeAxis;
