import { CountryFlag } from 'components/Flag';
import { max as d3Max, min as d3Min } from 'd3-array';

import { scaleLinear } from 'd3-scale';
import { useCo2ColorScale } from 'hooks/theme';
import { useMemo } from 'react';
import { useTranslation } from 'translation/translation';
import { ElectricityModeType, ZoneDetail, ZoneDetails, ZoneKey } from 'types';
import { modeColor } from 'utils/constants';
import { LABEL_MAX_WIDTH, PADDING_X } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import {
  ExchangeDataType,
  ProductionDataType,
  getDataBlockPositions,
  getElectricityProductionValue,
} from './utils';

interface BarElectricityBreakdownChartProps {
  height: number;
  width: number;
  data: ZoneDetails;
  currentData: ZoneDetail;
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

function BarElectricityBreakdownChart({
  data,
  currentData,
  exchangeData,
  height,
  isMobile,
  productionData,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  onExchangeRowMouseOver,
  onExchangeRowMouseOut,
  width,
}: BarElectricityBreakdownChartProps) {
  const { __ } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  const { productionY, exchangeY } = getDataBlockPositions(
    productionData.length,
    exchangeData
  );

  // Use the whole history to determine the min/max values in order to avoid
  // graph jumping while sliding through the time range.
  const [minPower, maxPower] = useMemo(() => {
    return [
      d3Min(
        Object.values(data.zoneStates).map((zoneData) =>
          Math.min(
            -zoneData.maxStorageCapacity || 0,
            -zoneData.maxStorage || 0,
            -zoneData.maxExport || 0,
            -zoneData.maxExportCapacity || 0
          )
        )
      ) || 0,
      d3Max(
        Object.values(data.zoneStates).map((zoneData) =>
          Math.max(
            zoneData.maxCapacity || 0,
            zoneData.maxProduction || 0,
            zoneData.maxDischarge || 0,
            zoneData.maxStorageCapacity || 0,
            zoneData.maxImport || 0,
            zoneData.maxImportCapacity || 0
          )
        )
      ) || 0,
    ];
  }, [data]);

  // Power in MW
  const powerScale = scaleLinear()
    .domain([minPower, maxPower])
    .range([0, width - LABEL_MAX_WIDTH - PADDING_X]);

  const formatTick = (t: number) => {
    const [x1, x2] = powerScale.domain();
    if (x2 - x1 <= 1) {
      return `${t * 1e3} kW`;
    }
    if (x2 - x1 <= 1e3) {
      return `${t} MW`;
    }
    return `${t * 1e-3} GW`;
  };

  return (
    <svg className="w-full overflow-visible" height={height}>
      <Axis formatTick={formatTick} height={height} scale={powerScale} />
      <g transform={`translate(0, ${productionY})`}>
        {productionData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={__(d.mode)}
            width={width}
            scale={powerScale}
            value={getElectricityProductionValue(d)}
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, currentData, event)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
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
      <g transform={`translate(0, ${exchangeY})`}>
        {exchangeData.map((d, index) => (
          <Row
            key={d.zoneKey}
            index={index}
            label={d.zoneKey}
            width={width}
            scale={powerScale}
            value={d.exchange}
            onMouseOver={(event) => onExchangeRowMouseOver(d.zoneKey, currentData, event)}
            onMouseOut={onExchangeRowMouseOut}
            isMobile={isMobile}
          >
            <CountryFlag zoneId={d.zoneKey} className="pointer-events-none" />

            <HorizontalBar
              className="capacity"
              fill="rgba(0, 0, 0, 0.15)"
              range={d.exchangeCapacityRange}
              scale={powerScale}
            />
            <HorizontalBar
              className="exchange"
              fill={co2ColorScale(d.gCo2eqPerkWh)}
              range={[0, d.exchange]}
              scale={powerScale}
            />
          </Row>
        ))}
      </g>
    </svg>
  );
}

export default BarElectricityBreakdownChart;
