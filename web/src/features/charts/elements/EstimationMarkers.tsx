import { scaleTime } from 'd3-scale';
import { area, curveStepAfter } from 'd3-shape';
import { useDarkMode } from 'hooks/theme';
import { useTranslation } from 'react-i18next';
import PulseLoader from 'react-spinners/PulseLoader';
import useResizeObserver from 'use-resize-observer/polyfilled';
import { EstimationMethods } from 'utils/constants';
import getEstimationOrAggregationTranslation from 'utils/getEstimationTranslation';

const DARK_MODE_PATTERN_STROKE = '#404040';
const LIGHT_MODE_PATTERN_STROKE = 'darkgray';
const MARKER_COLOR = 'lightgray';
const SHOW_MARKER = false;

export function EstimationLegendIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" className="mr-1">
      <rect width="24" height="24" fill="url(#pattern)" transform="scale(0.5)" />
      {SHOW_MARKER && (
        <line x1="0" y1="11" x2="12" y2="11" stroke={MARKER_COLOR} strokeWidth="2" />
      )}
    </svg>
  );
}

type EstimationLegendProps = {
  isAggregated: boolean;
  estimationMethod?: EstimationMethods;
  valueAxisLabel: string;
};

export function EstimationLegend({
  isAggregated,
  estimationMethod,
  valueAxisLabel,
}: EstimationLegendProps) {
  const { t } = useTranslation();
  return (
    <div className="mb-2 flex flex-row items-center justify-between text-xs text-[#8b8b8b] dark:text-[#848484]">
      <span className="flex">
        <EstimationLegendIcon />
        {getEstimationOrAggregationTranslation(
          t,
          'legend',
          isAggregated,
          estimationMethod
        )}
      </span>
      <span className="ml-auto">{valueAxisLabel}</span>
    </div>
  );
}

function EstimationMarkers({
  datetimes,
  scaleWidth,
  scaleHeight,
  className,
  transform,
  estimated,
  markerHeight = 3,
}: {
  datetimes: any[] | undefined;
  scaleWidth: number;
  scaleHeight: number;
  className?: string;
  transform?: string;
  estimated?: boolean[];
  markerHeight?: number;
}) {
  const { ref } = useResizeObserver<SVGSVGElement>();
  const isDarkMode = useDarkMode();

  if (datetimes === undefined || estimated == null) {
    return (
      <div className="flex h-[22px]  w-full justify-center">
        <PulseLoader size={6} color={'#135836'} />
      </div>
    );
  }

  const startDate = datetimes[0];
  const endDate = datetimes.at(-1);
  if (!startDate || !endDate) {
    return null; // No valid dates to render
  }
  const timeScale = scaleTime().domain([startDate, endDate]).range([0, scaleWidth]);

  const markerPathData = area()
    // see https://github.com/d3/d3-shape#curveStep
    .curve(curveStepAfter)
    .x((d: any) => timeScale(d))
    .y0(0)
    .y1((d, index) => (estimated?.at(index) ? markerHeight : 0));
  const backgroundPathData = area()
    .curve(curveStepAfter)
    .x((d: any) => timeScale(d))
    .y0(0)
    .y1((d, index) => (estimated?.at(index) ? -scaleHeight : 0));

  const patternStroke = isDarkMode ? DARK_MODE_PATTERN_STROKE : LIGHT_MODE_PATTERN_STROKE;
  const patternBackground = isDarkMode ? 'black' : 'white';

  return (
    <svg className={className} ref={ref}>
      <defs>
        <pattern
          id="pattern"
          width="8"
          height="8"
          viewBox="0 0 8 8"
          patternUnits="userSpaceOnUse"
        >
          <rect width="8" height="8" fill={patternBackground} />
          <path d="M-5 13L15 -7" stroke={patternStroke} />
          <path d="M-1 17L19 -3" stroke={patternStroke} />
          <path d="M-10 10L10 -10" stroke={patternStroke} />
        </pattern>
      </defs>
      {SHOW_MARKER && (
        <g
          fill={MARKER_COLOR}
          textAnchor="middle"
          transform={transform}
          style={{ pointerEvents: 'none' }}
        >
          <path d={markerPathData(datetimes) || undefined} />
        </g>
      )}
      <g textAnchor="middle" transform={transform} style={{ pointerEvents: 'none' }}>
        <path
          d={backgroundPathData(datetimes) || undefined}
          fill="url(#pattern)"
          opacity={0.4}
        />
      </g>
    </svg>
  );
}

export default EstimationMarkers;
