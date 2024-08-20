import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useMemo } from 'react';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { formatCo2 } from 'utils/formatting';

import BarEmissionExchangeChart from './BarEmissionExchangeChart';
import { BarEmissionProductionChart } from './BarEmissionProductionChart';
import { EXCHANGE_PADDING, LABEL_MAX_WIDTH, PADDING_X } from './constants';
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

    return formatCo2({ value: t, total: maxValue });
  };

  return (
    <>
      <BarEmissionProductionChart
        height={height}
        formatTick={formatTick}
        co2Scale={co2Scale}
        productionY={productionY}
        productionData={productionData}
        data={data}
        width={width}
        onProductionRowMouseOut={onProductionRowMouseOut}
        onProductionRowMouseOver={onProductionRowMouseOver}
        isMobile={isMobile}
      />
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
