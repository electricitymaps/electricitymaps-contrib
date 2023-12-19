/* eslint-disable unicorn/no-array-reduce */
import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { ExchangeArrowData, GridState, StateExchangeData } from 'types';
import { SpatialAggregate, TimeAverages } from 'utils/constants';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

import exchangesConfigJSON from '../../config/exchanges.json'; // do something globally
import exchangesToExclude from '../../config/excluded_aggregated_exchanges.json'; // do something globally

// TODO: set up proper typed method for retrieving config files.
const exchangesConfig: Record<string, any> = exchangesConfigJSON;

export function useExchangeArrowsData(): ExchangeArrowData[] {
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [viewMode] = useAtom(spatialAggregateAtom);
  const { data, isError, isLoading } = useGetState();
  const [mode] = useAtom(productionConsumptionAtom);
  const isConsumption = mode === 'consumption';
  const isHourly = timeAverage === TimeAverages.HOURLY;

  const exchangesToUse: { [key: string]: StateExchangeData } = useMemo(() => {
    if (!data) {
      return {};
    }
    const grid = data as GridState;

    const exchanges = grid?.data?.datetimes?.[selectedDatetime?.datetimeString]?.e;
    if (!exchanges) {
      return [];
    }

    const exchangesToExcludeZoneViewSet = new Set(
      exchangesToExclude.exchangesToExcludeZoneView
    );
    const exchangesToExcludeCountryViewSet = new Set(
      exchangesToExclude.exchangesToExcludeCountryView
    );

    let zoneViewExchanges = {};
    let countryViewExchanges = {};

    for (const key of Object.keys(exchanges)) {
      if (!exchangesToExcludeZoneViewSet.has(key)) {
        zoneViewExchanges = { ...zoneViewExchanges, [key]: exchanges[key] };
      }
      if (!exchangesToExcludeCountryViewSet.has(key)) {
        countryViewExchanges = { ...countryViewExchanges, [key]: exchanges[key] };
      }
    }

    return viewMode === SpatialAggregate.COUNTRY
      ? countryViewExchanges
      : zoneViewExchanges;
  }, [viewMode, data]);

  if (isError || isLoading || !isConsumption || !isHourly) {
    return [];
  }

  const exchanges = data.data.datetimes[selectedDatetime.datetimeString].e;

  const currentExchanges: ExchangeArrowData[] = Object.entries(exchangesToUse)
    .filter(([key]) => exchanges[key] !== undefined)
    .map(([key, value]) => ({
      ...value,
      ...exchangesConfig[key],
      key: key,
    }));

  return currentExchanges;
}
