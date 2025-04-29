import { scaleTime } from 'd3-scale';
import { area, curveStepAfter } from 'd3-shape';
import PulseLoader from 'react-spinners/PulseLoader';
import useResizeObserver from 'use-resize-observer/polyfilled';

function EstimationMarkers({ datetimes, scaleWidth, className, transform, estimated }) {
  const { ref } = useResizeObserver<SVGSVGElement>();

  if (datetimes === undefined || estimated == null) {
    return (
      <div className="flex h-[22px]  w-full justify-center">
        <PulseLoader size={6} color={'#135836'} />
      </div>
    );
  }

  const startDate = datetimes[0];
  const endDate = datetimes.at(-1);
  const timeScale = scaleTime().domain([startDate, endDate]).range([0, scaleWidth]);

  const layerArea = area()
    // see https://github.com/d3/d3-shape#curveStep
    .curve(curveStepAfter)
    .x(timeScale)
    .y0(0)
    .y1(3)
    .defined((d, index) => estimated?.at(index));

  return (
    <svg className={className} ref={ref}>
      <g
        fill="orange"
        textAnchor="middle"
        transform={transform}
        style={{ pointerEvents: 'none' }}
      >
        <path d={layerArea(datetimes)} />
      </g>
    </svg>
  );
}

export default EstimationMarkers;
