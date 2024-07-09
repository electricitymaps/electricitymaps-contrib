import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType, ZoneDetail, ZoneDetails, ZoneKey } from 'types';
import { modeColor, TimeAverages } from 'utils/constants';
import { formatEnergy, formatPower } from 'utils/formatting';
import { timeAverageAtom } from 'utils/state/atoms';

import ProductionSourceLegend from '../ProductionSourceLegend';
import BarElectricityExchangeChart from './BarElectricityExchangeChart';
import { EXCHANGE_PADDING, LABEL_MAX_WIDTH, PADDING_X } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import {
  ExchangeDataType,
  getDataBlockPositions,
  getElectricityProductionValue,
  ProductionDataType,
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
  graphUnit: string;
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
  graphUnit,
}: BarElectricityBreakdownChartProps) {
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  const { productionY, exchangeHeight } = getDataBlockPositions(
    productionData.length,
    exchangeData
  );
  const [timeAverage] = useAtom(timeAverageAtom);
  const isHourly = timeAverage === TimeAverages.HOURLY;

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
    // Use same unit as max value for tick with value 0
    if (t === 0) {
      const tickValue = isHourly ? formatPower(maxPower, 1) : formatEnergy(maxPower, 1);
      return tickValue.toString().replace(/[\d.]+/, '0');
    }
    return isHourly ? formatPower(t, 2) : formatEnergy(t, 2);
  };

  return (
    <>
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
              onMouseOver={(event) =>
                onProductionRowMouseOver(d.mode, currentData, event)
              }
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
      <BarElectricityExchangeChart
        height={exchangeHeight + EXCHANGE_PADDING}
        onExchangeRowMouseOut={onExchangeRowMouseOut}
        onExchangeRowMouseOver={onExchangeRowMouseOver}
        exchangeData={exchangeData}
        data={currentData}
        width={width}
        powerScale={powerScale}
        formatTick={formatTick}
        co2ColorScale={co2ColorScale}
        graphUnit={graphUnit}
      />
    </>
  );
}

export default BarElectricityBreakdownChart;
