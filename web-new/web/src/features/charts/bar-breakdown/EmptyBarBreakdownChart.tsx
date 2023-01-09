import { scaleLinear } from 'd3-scale';
import { useMemo } from 'react';
import { useTranslation } from 'translation/translation';
import { modeOrder } from 'utils/constants';
import { LABEL_MAX_WIDTH, PADDING_X } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
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
  const productionData = modeOrder.map((d) => ({
    mode: d,
    tCo2eqPerMin: 0,
    tCo2eqPerMinByFuel: {},
    tCo2eqPerMinByFuelAndSource: {},
    isStorage: false,
  }));
  const { __ } = useTranslation();
  const { productionY } = getDataBlockPositions(0, []);

  const maxCO2eqExport = 1;
  const maxCO2eqImport = 10;
  const maxCO2eqProduction = 10;

  // in tCO₂eq/min
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
  const formatTick = (t: number) => {
    // TODO: format tick depending on displayByEmissions
    return `${t} GW`;
  };

  return (
    <>
      <div style={{ width, height, position: 'absolute' }}>
        {overLayText && (
          <div className="absolute top-[50%] left-[50%] z-10 -translate-x-1/2 -translate-y-1/2 rounded-sm bg-gray-200 p-2 text-center text-sm shadow-sm dark:bg-gray-900">
            {overLayText}
          </div>
        )}
      </div>
      <svg
        className={`${
          overLayText ? 'opacity-40' : 'opacity-1'
        } w-full overflow-visible text-md`}
        height={height}
      >
        <Axis formatTick={formatTick} height={height} scale={co2Scale} />
        <g transform={`translate(0, ${productionY})`}>
          {productionData.map((d, index) => (
            <Row
              key={d.mode}
              index={index}
              label={__(d.mode)}
              width={width}
              scale={co2Scale}
              value={Math.abs(d.tCo2eqPerMin)}
              isMobile={Boolean(isMobile)}
            >
              <HorizontalBar
                className="production"
                fill="lightgray"
                range={[0, Math.floor(Math.random() * 10)]}
                scale={co2Scale}
              />
            </Row>
          ))}
        </g>
      </svg>
    </>
  );
}

export default EmptyBarBreakdownChart;
