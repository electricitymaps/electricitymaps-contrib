import useGetZone from 'api/getZone';
import { useAtomValue } from 'jotai';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { SpatialAggregate } from 'utils/constants';
import {
  isConsumptionAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';

import {
  getDataBlockPositions,
  getExchangeData,
  getExchangesToDisplay,
  getProductionData,
} from '../bar-breakdown/utils';

const DEFAULT_BAR_PX_HEIGHT = 265;

export default function useBarBreakdownChartData() {
  // TODO: Create hook for using "current" selectedTimeIndex of data instead
  const { data: zoneData, isLoading } = useGetZone();
  const { zoneId } = useParams<RouteParameters>();
  const viewMode = useAtomValue(spatialAggregateAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const isCountryView = viewMode === SpatialAggregate.COUNTRY;
  const currentData = zoneData?.zoneStates?.[selectedDatetimeString];
  const isConsumption = useAtomValue(isConsumptionAtom);

  const productionData = useMemo(() => getProductionData(currentData), [currentData]);

  const exchangeKeys = useMemo(
    () => getExchangesToDisplay(isCountryView, zoneId, zoneData?.zoneStates),
    [isCountryView, zoneId, zoneData?.zoneStates]
  );

  const exchangeData = useMemo(
    () => getExchangeData(exchangeKeys, isConsumption, currentData),
    [exchangeKeys, isConsumption, currentData]
  );

  if (isLoading) {
    return { isLoading };
  }

  if (!zoneId || !zoneData || !selectedDatetimeString || !currentData) {
    return {
      height: DEFAULT_BAR_PX_HEIGHT,
      zoneDetails: undefined,
      currentZoneDetail: undefined,
      exchangeData: [],
      productionData: [],
      isLoading: false,
    };
  }

  const { exchangeY } = getDataBlockPositions(
    //TODO this naming could be more descriptive
    productionData.length,
    exchangeData
  );
  return {
    height: exchangeY,
    zoneDetails: zoneData, // TODO: Data is returned here just to pass it back to the tooltip
    currentZoneDetail: currentData,
    exchangeData,
    productionData,
    isLoading: false,
  };
}
