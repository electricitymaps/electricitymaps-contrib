import { ScaleLinear } from 'd3-scale';
import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import { FormatTick } from './BarElectricityBreakdownChart';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import { ProductionSourceRow } from './elements/Row';
import { ProductionDataType } from './utils';

export function BarEmissionProductionChart({
  height,
  formatTick,
  co2Scale,
  productionY,
  productionData,
  width,
  onProductionRowMouseOut,
  onProductionRowMouseOver,
  isMobile,
}: {
  height: number;
  formatTick: FormatTick;
  co2Scale: ScaleLinear<number, number, never>;
  productionY: number;
  productionData: ProductionDataType[];
  width: number;
  onProductionRowMouseOut: () => void;
  onProductionRowMouseOver: (
    rowKey: ElectricityModeType,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  isMobile: boolean;
}) {
  return (
    <svg className="w-full overflow-visible" height={height}>
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
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, event)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={[0, Math.abs(d.gCo2eq)]}
              scale={co2Scale}
            />
          </ProductionSourceRow>
        ))}
      </g>
    </svg>
  );
}
