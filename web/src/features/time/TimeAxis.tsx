import { ScaleTime, scaleTime } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import PulseLoader from 'react-spinners/PulseLoader';
import useResizeObserver from 'use-resize-observer/polyfilled';
import { TimeAverages } from 'utils/constants';

import { formatDateTick } from '../../utils/formatting';

// Frequency at which values are displayed for a tick
const TIME_TO_TICK_FREQUENCY = {
  hourly: 6,
  daily: 6,
  monthly: 1,
  yearly: 1,
};

const renderTick = (
  scale: ScaleTime<number, number>,
  value: Date,
  index: number,
  displayLive: boolean,
  lang: string,
  selectedTimeAggregate: TimeAverages,
  isLoading: boolean,
  latestString: string,
  isGraph: boolean
) => {
  const shouldShowValue =
    index % TIME_TO_TICK_FREQUENCY[selectedTimeAggregate] === 0 && !isLoading;
  const valueOpacity = isGraph ? 0.5 : 1;
  return (
    <g
      key={`timeaxis-tick-${index}`}
      className="text-xs"
      opacity={1}
      transform={`translate(${scale(value)},0)`}
    >
      <line stroke="currentColor" y2="6" opacity={shouldShowValue ? valueOpacity : 0.2} />
      {shouldShowValue &&
        renderTickValue(
          value,
          index,
          displayLive,
          lang,
          selectedTimeAggregate,
          latestString,
          isGraph
        )}
    </g>
  );
};

const renderTickValue = (
  v: Date,
  index: number,
  displayLive: boolean,
  lang: string,
  selectedTimeAggregate: TimeAverages,
  latestString: string,
  isGraph: boolean
) => {
  const shouldDisplayLive = index === 24 && displayLive;
  const fontWeight = isGraph ? 'normal' : 'bold';
  return (
    <text
      fill="currentColor"
      y="9"
      dy="0.71em"
      fontWeight={fontWeight}
      fontSize={'0.65rem'}
    >
      {shouldDisplayLive ? latestString : formatDateTick(v, lang, selectedTimeAggregate)}
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
  isGraph?: boolean;
}

function TimeAxis({
  selectedTimeAggregate,
  datetimes,
  isLoading,
  transform,
  scaleWidth,
  isLiveDisplay,
  className,
  isGraph = true,
}: TimeAxisProps) {
  const { t, i18n } = useTranslation();
  const { ref, width: observerWidth = 0 } = useResizeObserver<SVGSVGElement>();

  const width = observerWidth - 24;

  if (datetimes === undefined || isLoading) {
    return (
      <div className="flex h-[22px] w-full justify-center">
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
          renderTick(
            scale,
            v,
            index,
            isLiveDisplay ?? false,
            i18n.language,
            selectedTimeAggregate,
            isLoading,
            t('time-controller.latest'),
            isGraph
          )
        )}
      </g>
    </svg>
  );
}

export default TimeAxis;
