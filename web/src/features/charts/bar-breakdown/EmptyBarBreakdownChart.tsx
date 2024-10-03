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
  isMobile?: boolean;
  overLayText?: string;
}

function EmptyBarBreakdownChart({
  height,
  isMobile,
  overLayText,
  width,
}: EmptyBarBreakdownChartProps) {
  const productionData = modeOrderBarBreakdown.map((d) => ({
    mode: d,
    gCo2eq: 0,
    gCo2eqByFuel: {},
    gCo2eqByFuelAndSource: {},
    isStorage: false,
  }));
  const { productionY } = getDataBlockPositions(0, []);

  const maxCO2eqExport = 1;
  const maxCO2eqImport = 10;
  const maxCO2eqProduction = 10;

  // in CO₂eq
  const co2Scale = useMemo(
    () =>
      scaleLinear()
        .domain([
          -maxCO2eqExport || 0,
          Math.max(maxCO2eqProduction || 0, maxCO2eqImport || 0),
        ])
        .range([0, width - LABEL_MAX_WIDTH - PADDING_X]),
    [maxCO2eqExport, maxCO2eqProduction, maxCO2eqImport, width]
  );

  // eslint-disable-next-line unicorn/consistent-function-scoping
  const formatTick = (t: number) =>
    // TODO: format tick depending on displayByEmissions
    `${t} ${PowerUnits.GIGAWATTS}`;
  return (
    <>
      <div style={{ width, height, position: 'absolute' }}>
        {overLayText && (
          <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-sm bg-gray-200 p-2 text-center text-sm shadow-sm dark:bg-gray-900">
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
        <g transform={`translate(0, ${productionY})`}>
          {productionData.map((d, index) => (
            <ProductionSourceRow
              key={d.mode}
              index={index}
              productionMode={d.mode}
              width={width}
              scale={co2Scale}
              value={Math.abs(d.gCo2eq)}
              isMobile={Boolean(isMobile)}
            >
              <HorizontalBar
                className="production"
                fill="lightgray"
                range={[0, Math.floor(Math.random() * 10)]}
                scale={co2Scale}
              />
            </ProductionSourceRow>
          ))}
        </g>
      </svg>
    </>
  );
}

export default EmptyBarBreakdownChart;
