import { ScaleLinear } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import ProductionSourceLegend from '../ProductionSourceLegend';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
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
  formatTick: (value: number) => string;
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
  const { t } = useTranslation();
  return (
    <svg className="w-full overflow-visible" height={height}>
      <Axis formatTick={formatTick} height={height} scale={co2Scale} />
      <g transform={`translate(0, ${productionY})`}>
        {productionData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={t(d.mode)}
            width={width}
            scale={co2Scale}
            value={Math.abs(d.gCo2eq)}
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, event)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <ProductionSourceLegend electricityType={d.mode} />
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={[0, Math.abs(d.gCo2eq)]}
              scale={co2Scale}
            />
          </Row>
        ))}
      </g>
    </svg>
  );
}
