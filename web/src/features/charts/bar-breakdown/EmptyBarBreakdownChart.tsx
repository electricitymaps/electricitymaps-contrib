import { Group } from '@visx/group';
import { scaleLinear } from 'd3-scale';
import { useMemo } from 'react';
import { modeOrderBarBreakdown } from 'utils/constants';
import { PowerUnits } from 'utils/units';

import { LABEL_MAX_WIDTH, PADDING_X } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import { ProductionSourceRow } from './elements/Row';
import { getDataBlockPositions } from './utils';

interface EmptyBarBreakdownChartProps {
  height: number;
  width: number;
  isMobile: boolean;
  overLayText?: string;
}

const MAX_CO2EQ = 10;
const MIN_CO2EQ = -1;

const formatTick = (t: number) =>
  // TODO: format tick depending on displayByEmissions
  `${t} ${PowerUnits.GIGAWATTS}`;

function EmptyBarBreakdownChart({
  height,
  isMobile,
  overLayText,
  width,
}: EmptyBarBreakdownChartProps) {
  const { productionY } = getDataBlockPositions(0, []);

  // in CO₂eq
  const co2Scale = useMemo(
    () =>
      scaleLinear()
        .domain([MIN_CO2EQ, MAX_CO2EQ])
        .range([0, width - LABEL_MAX_WIDTH - PADDING_X]),
    [width]
  );

  return (
    <>
      <div style={{ width, height, position: 'absolute' }}>
        {overLayText && (
          <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-sm bg-neutral-200 p-2 text-center text-sm shadow-sm dark:bg-neutral-900">
            {overLayText}
          </div>
        )}
      </div>
      <svg
        className={`${
          overLayText ? 'opacity-40' : 'opacity-1'
        } text-md w-full overflow-visible`}
        height={height}
      >
        <Axis formatTick={formatTick} height={height} scale={co2Scale} />
        <Group top={productionY}>
          {modeOrderBarBreakdown.map((mode, index) => (
            <ProductionSourceRow
              key={mode}
              index={index}
              productionMode={mode}
              width={width}
              value={0}
              capacity={0}
              isMobile={isMobile}
            >
              <HorizontalBar
                className="production"
                fill="lightgray"
                range={[0, Math.floor(Math.random() * 10)]}
                scale={co2Scale}
              />
            </ProductionSourceRow>
          ))}
        </Group>
      </svg>
    </>
  );
}

export default EmptyBarBreakdownChart;
