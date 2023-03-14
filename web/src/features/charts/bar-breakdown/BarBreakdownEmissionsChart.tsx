import { CountryFlag } from 'components/Flag';
import { max as d3Max } from 'd3-array';

import { scaleLinear } from 'd3-scale';
import { useMemo } from 'react';
import { useTranslation } from 'translation/translation';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { modeColor } from 'utils/constants';
import { LABEL_MAX_WIDTH, PADDING_X } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import { ExchangeDataType, ProductionDataType, getDataBlockPositions } from './utils';

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
  const { __ } = useTranslation();
  const { productionY, exchangeY } = getDataBlockPositions(
    productionData.length > 0 ? productionData.length : 0,
    exchangeData
  );

  const maxCO2eqExport = d3Max(exchangeData, (d) => Math.max(0, -d.tCo2eqPerMin)) || 0;
  const maxCO2eqImport = d3Max(exchangeData, (d) => Math.max(0, d.tCo2eqPerMin));
  const maxCO2eqProduction = d3Max(productionData, (d) => d.tCo2eqPerMin);

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

  const formatTick = (t: number) => {
    const [x1, x2] = co2Scale.domain();
    if (x2 - x1 <= 1) {
      return `${t * 1e3} kg/min`;
    }
    return `${t} t/min`;
  };

  return (
    <svg className="w-full overflow-visible" height={height}>
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
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, data, event)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={[0, Math.abs(d.tCo2eqPerMin)]}
              scale={co2Scale}
            />
          </Row>
        ))}
      </g>
      <g transform={`translate(0, ${exchangeY})`}>
        {exchangeData.map((d, index) => (
          <Row
            key={d.zoneKey}
            index={index}
            label={d.zoneKey}
            width={width}
            scale={co2Scale}
            value={d.exchange}
            onMouseOver={(event) => onExchangeRowMouseOver(d.zoneKey, data, event)}
            onMouseOut={onExchangeRowMouseOut}
            isMobile={isMobile}
          >
            <CountryFlag zoneId={d.zoneKey} className="pointer-events-none" />
            <HorizontalBar
              className="exchange"
              fill={'gray'}
              range={[0, d.tCo2eqPerMin]}
              scale={co2Scale}
            />
          </Row>
        ))}
      </g>
    </svg>
  );
}

export default BarBreakdownEmissionsChart;
