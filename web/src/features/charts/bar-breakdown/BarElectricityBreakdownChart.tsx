import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { memo, useCallback, useMemo } from 'react';
import { ElectricityModeType, ZoneDetails, ZoneKey } from 'types';
import { formatEnergy, formatPower } from 'utils/formatting';
import { isFineGranularityAtom } from 'utils/state/atoms';

import BarElectricityExchangeChart from './BarElectricityExchangeChart';
import BarElectricityProductionChart from './BarElectricityProductionChart';
import { EXCHANGE_PADDING, LABEL_MAX_WIDTH, PADDING_X } from './constants';
import { FormatTick } from './elements/Axis';
import { ExchangeDataType, getDataBlockPositions, ProductionDataType } from './utils';

interface BarElectricityBreakdownChartProps {
  height: number;
  width: number;
  data: ZoneDetails;
  exchangeData: ExchangeDataType[];
  productionData: ProductionDataType[];
  isMobile: boolean;
  onProductionRowMouseOver: (
    rowKey: ElectricityModeType,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onProductionRowMouseOut: () => void;
  onExchangeRowMouseOver: (
    rowKey: ZoneKey,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onExchangeRowMouseOut: () => void;
  graphUnit: string | undefined;
}
const NUMERIC_REGEX = /[\d.]+/;

function BarElectricityBreakdownChart({
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
  graphUnit,
}: BarElectricityBreakdownChartProps) {
  const co2ColorScale = useCo2ColorScale();
  const { productionY, exchangeHeight } = getDataBlockPositions(
    productionData.length,
    exchangeData
  );
  const isFineGranularity = useAtomValue(isFineGranularityAtom);

  // Use the whole history to determine the min/max values in order to avoid
  // graph jumping while sliding through the time range.
  const [minPower, maxPower] = useMemo(
    () => [
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
    ],
    [data]
  );

  // Power in MW
  const powerScale = useMemo(
    () =>
      scaleLinear()
        .domain([minPower, maxPower])
        .range([0, width - LABEL_MAX_WIDTH - PADDING_X]),
    [minPower, maxPower, width]
  );

  const formatTick: FormatTick = useCallback(
    (t: number) => {
      // Use same unit as max value for tick with value 0
      if (t === 0) {
        const tickValue = isFineGranularity
          ? formatPower({ value: maxPower, numberDigits: 1 })
          : formatEnergy({ value: maxPower, numberDigits: 1 });
        return tickValue.toString().replace(NUMERIC_REGEX, '0');
      }
      return isFineGranularity
        ? formatPower({ value: t, numberDigits: 2 })
        : formatEnergy({ value: t, numberDigits: 2 });
    },
    [isFineGranularity, maxPower]
  );
  return (
    <>
      <BarElectricityProductionChart
        powerScale={powerScale}
        height={height}
        formatTick={formatTick}
        productionY={productionY}
        productionData={productionData}
        width={width}
        onProductionRowMouseOver={onProductionRowMouseOver}
        onProductionRowMouseOut={onProductionRowMouseOut}
        isMobile={isMobile}
      />
      <BarElectricityExchangeChart
        height={exchangeHeight + EXCHANGE_PADDING}
        onExchangeRowMouseOut={onExchangeRowMouseOut}
        onExchangeRowMouseOver={onExchangeRowMouseOver}
        exchangeData={exchangeData}
        width={width}
        powerScale={powerScale}
        formatTick={formatTick}
        co2ColorScale={co2ColorScale}
        graphUnit={graphUnit}
      />
    </>
  );
}

export default memo(BarElectricityBreakdownChart);
