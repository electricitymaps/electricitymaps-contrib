import useGetZone from 'api/getZone';
import { useAtom } from 'jotai';
import { useParams } from 'react-router-dom';
import { ToggleOptions } from 'utils/constants';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';
import {
  getDataBlockPositions,
  getExchangeData,
  getExchangesToDisplay,
  getProductionData,
} from '../bar-breakdown/utils';

export default function useBarBreakdownChartData() {
  // TODO: Create hook for using "current" selectedTimeIndex of data instead
  const { data: zoneData, isLoading } = useGetZone();
  const { zoneId } = useParams();
  const [aggregateToggle] = useAtom(spatialAggregateAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);
  const isAggregateToggled = aggregateToggle === ToggleOptions.ON;
  const currentData = zoneData?.zoneStates?.[selectedDatetime.datetimeString];
  if (
    isLoading ||
    !zoneId ||
    !zoneData ||
    !selectedDatetime.datetimeString ||
    !currentData
  ) {
    return {
      height: 0,
      zoneDetails: undefined,
      currentZoneDetail: undefined,
      exchangeData: [],
      productionData: [],
      isLoading: true,
    };
  }

  const exchangeKeys = getExchangesToDisplay(
    zoneId,
    isAggregateToggled,
    currentData.exchange
  );

  const productionData = getProductionData(currentData); // TODO: Consider memoing this
  const exchangeData = getExchangeData(currentData, exchangeKeys, mixMode); // TODO: Consider memoing this

  const { exchangeY, exchangeHeight } = getDataBlockPositions(
    productionData.length,
    exchangeData
  );
  const height = exchangeY + exchangeHeight;

  return {
    height,
    zoneDetails: zoneData, // TODO: Data is returned here just to pass it back to the tooltip
    currentZoneDetail: currentData,
    exchangeData,
    productionData,
    isLoading: false,
  };
}
