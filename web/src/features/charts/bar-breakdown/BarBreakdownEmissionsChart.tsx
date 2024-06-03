import { CountryFlag } from 'components/Flag';
import { max as d3Max } from 'd3-array';
import { ScaleLinear, scaleLinear } from 'd3-scale';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { modeColor } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';

import { LABEL_MAX_WIDTH, PADDING_X } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import ProductionSourceLegend from './ProductionSourceLegend';
import { ExchangeDataType, getDataBlockPositions, ProductionDataType } from './utils';

interface BarBreakdownEmissionsChartProps {
  co2Scale: ScaleLinear<number, number, never>;
  formatTick: (value: number) => string;
  productionY: number;
  height: number;
  width: number;
  data: ZoneDetail;
  productionData: ProductionDataType[];
  isMobile: boolean;
  onProductionRowMouseOver: (
    rowKey: ElectricityModeType,
    data: ZoneDetail,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onProductionRowMouseOut: () => void;
}

function BarBreakdownEmissionsChart({
  co2Scale,
  formatTick,
  productionY,
  data,
  height,
  isMobile,
  productionData,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  width,
}: BarBreakdownEmissionsChartProps) {
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
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, data, event)}
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

export default BarBreakdownEmissionsChart;
