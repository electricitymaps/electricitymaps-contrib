import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { modeColor } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';

import ProductionSourceLegend from '../ProductionSourceLegend';
import BarEmissionExchangeChart from './BarEmissionExchangeChart';
import {
  AXIS_LEGEND_PADDING,
  EXCHANGE_PADDING,
  LABEL_MAX_WIDTH,
  PADDING_X,
} from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import { ExchangeDataType, getDataBlockPositions, ProductionDataType } from './utils';

interface BarBreakdownEmissionsChartProps {
  height: number;
  width: number;
  data: ZoneDetail;
  exchangeData: ExchangeDataType[];
  productionData: ProductionDataType[];
  isMobile: boolean;
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

function BarBreakdownEmissionsChart({
  data,
  exchangeData,
  height,
  isMobile,
  productionData,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  onExchangeRowMouseOver,
  onExchangeRowMouseOut,
  width,
}: BarBreakdownEmissionsChartProps) {
  const { t } = useTranslation();

  const { productionY, exchangeHeight } = getDataBlockPositions(
    productionData.length > 0 ? productionData.length : 0,
    exchangeData
  );

  const maxCO2eqExport = d3Max(exchangeData, (d) => Math.max(0, -d.gCo2eq)) || 0;
  const maxCO2eqImport = d3Max(exchangeData, (d) => Math.max(0, d.gCo2eq));
  const maxCO2eqProduction = d3Max(productionData, (d) => d.gCo2eq);

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

  const formatTick = (t: number) => {
    const maxValue = maxCO2eqProduction || 1;

    return formatCo2(t, maxValue);
  };

  return (
    <>
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
      <BarEmissionExchangeChart
        height={exchangeHeight + EXCHANGE_PADDING}
        onExchangeRowMouseOut={onExchangeRowMouseOut}
        onExchangeRowMouseOver={onExchangeRowMouseOver}
        exchangeData={exchangeData}
        data={data}
        width={width}
        co2Scale={co2Scale}
        formatTick={formatTick}
      />
    </>
  );
}

export default BarBreakdownEmissionsChart;
