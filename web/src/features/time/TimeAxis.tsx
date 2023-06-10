import { ScaleTime, scaleTime } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import PulseLoader from 'react-spinners/PulseLoader';
import { TimeAverages } from 'utils/constants';
import { useReferenceWidthHeightObserver } from 'utils/viewport';
import { formatDateTick } from '../../utils/formatting';

// Frequency at which values are displayed for a tick
const TIME_TO_TICK_FREQUENCY = {
  hourly: 6,
  daily: 6,
  monthly: 1,
  yearly: 1,
};

const renderTick = (
  scale: any,
  value: Date,
  index: number,
  displayLive: boolean,
  lang: string,
  selectedTimeAggregate: TimeAverages,
  isLoading: boolean
) => {
  const shouldShowValue =
    index % TIME_TO_TICK_FREQUENCY[selectedTimeAggregate] === 0 && !isLoading;
  return (
    <g
      key={`timeaxis-tick-${index}`}
      className="text-xs"
      opacity={1}
      transform={`translate(${scale(value)},0)`}
    >
      <line stroke="currentColor" y2="6" opacity={shouldShowValue ? 0.5 : 0.2} />
      {shouldShowValue &&
        renderTickValue(value, index, displayLive, lang, selectedTimeAggregate)}
    </g>
  );
};

const renderTickValue = (
  v: Date,
  index: number,
  displayLive: boolean,
  lang: string,
  selectedTimeAggregate: TimeAverages
) => {
  const shouldDisplayLive = index === 24 && displayLive;
  return shouldDisplayLive ? (
    <g>
      <circle cx="-1em" cy="1.15em" r="2" fill="red" />
      <text fill="#DE3054" y="9" x="5" dy="0.71em" fontWeight="bold">
        LIVE
      </text>
    </g>
  ) : (
    <text fill="currentColor" y="9" x="5" dy="0.71em">
      {formatDateTick(v, lang, selectedTimeAggregate)}
    </text>
  );
};

const getTimeScale = (rangeEnd: number, startDate: Date, endDate: Date) =>
  scaleTime().domain([startDate, endDate]).range([0, rangeEnd]);

interface TimeAxisProps {
  selectedTimeAggregate: TimeAverages;
  datetimes: Date[] | undefined;
  isLoading: boolean;
  scale?: ScaleTime<number, number>;
  isLiveDisplay?: boolean;
  transform?: string;
  scaleWidth?: number;
  className?: string;
}

function TimeAxis({
  selectedTimeAggregate,
  datetimes,
  isLoading,
  transform,
  scaleWidth,
  isLiveDisplay,
  className,
}: TimeAxisProps) {
  const { i18n } = useTranslation();
  const { ref, width } = useReferenceWidthHeightObserver(24);

  if (datetimes === undefined || isLoading) {
    return (
      <div className="flex h-[22px]  w-full justify-center">
        <PulseLoader size={6} color={'#135836'} />
      </div>
    );
  }

  const scale = getTimeScale(
    scaleWidth ?? width,
    datetimes[0],
    datetimes[datetimes.length - 1]
  );
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
          renderTick(
            scale,
            v,
            index,
            isLiveDisplay ?? false,
            i18n.language,
            selectedTimeAggregate,
            isLoading
          )
        )}
      </g>
    </svg>
  );
}

export default TimeAxis;
