import { ScaleLinear } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { modeColor } from 'utils/constants';

import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import ProductionSourceLegend from './ProductionSourceLegend';
import { getElectricityProductionValue, ProductionDataType } from './utils';

interface BarElectricityBreakdownChartProps {
  height: number;
  width: number;
  currentData: ZoneDetail;
  productionData: ProductionDataType[];
  isMobile: boolean;
  formatTick: (t: number) => string | number;
  powerScale: ScaleLinear<number, number, never>;
  productionY: number;
  onProductionRowMouseOver: (
    rowKey: ElectricityModeType,
    data: ZoneDetail,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onProductionRowMouseOut: () => void;
  onExchangeRowMouseOver: (
    rowKey: ZoneKey,
    data: ZoneDetail,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onExchangeRowMouseOut: () => void;
}

function BarElectricityBreakdownChart({
  currentData,
  height,
  isMobile,
  productionData,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  width,
  formatTick,
  powerScale,
  productionY,
}: BarElectricityBreakdownChartProps) {
  const { t } = useTranslation();

  return (
    <svg className="w-full overflow-visible" height={height}>
      <Axis formatTick={formatTick} height={height} scale={powerScale} />
      <g transform={`translate(0, ${productionY})`}>
        {productionData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={t(d.mode)}
            width={width}
            scale={powerScale}
            value={getElectricityProductionValue(d)}
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, currentData, event)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <ProductionSourceLegend electricityType={d.mode} />
            <HorizontalBar
              className="text-black/10 dark:text-white/10"
              fill="currentColor"
              range={d.isStorage ? [-(d.capacity || 0), d.capacity] : [0, d.capacity]}
              scale={powerScale}
            />
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={[0, getElectricityProductionValue(d)]}
              scale={powerScale}
            />
          </Row>
        ))}
      </g>
    </svg>
  );
}

export default BarElectricityBreakdownChart;
