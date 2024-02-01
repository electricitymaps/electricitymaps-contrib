/* eslint-disable unicorn/no-array-reduce */
import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { ExchangeArrowData, ExchangeResponse } from 'types';
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
const { exchangesToExcludeZoneView, exchangesToExcludeCountryView } = exchangesToExclude;

function filterExchanges(
  exchanges: Record<string, ExchangeResponse>,
  exclusionArray: string[]
): Record<string, ExchangeResponse> {
  const result: Record<string, ExchangeResponse> = {};
  const keys = Object.keys(exchanges).filter((key) => !exclusionArray.includes(key));
  for (const key of keys) {
    result[key] = exchanges[key];
  }
  return result;
}

export function useExchangeArrowsData(): ExchangeArrowData[] {
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [viewMode] = useAtom(spatialAggregateAtom);
  const { data, isError, isLoading } = useGetState();
  const [mode] = useAtom(productionConsumptionAtom);
  const isConsumption = mode === 'consumption';
  const isHourly = timeAverage === TimeAverages.HOURLY;

  const exchangesToUse: { [key: string]: ExchangeResponse } = useMemo(() => {
    const exchanges = data?.data.exchanges;

    if (!exchanges) {
      return {};
    }

    const zoneViewExchanges = filterExchanges(exchanges, exchangesToExcludeZoneView);
    const countryViewExchanges = filterExchanges(
      exchanges,
      exchangesToExcludeCountryView
    );

    return viewMode === SpatialAggregate.COUNTRY
      ? countryViewExchanges
      : zoneViewExchanges;
  }, [viewMode, data]);

  if (isError || isLoading || !isConsumption || !isHourly) {
    return [];
  }

  const exchanges = data?.data.exchanges;

  const currentExchanges: ExchangeArrowData[] = Object.entries(exchangesToUse)
    .filter(([key]) => exchanges[key][selectedDatetime.datetimeString] !== undefined)
    .map(([key, value]) => ({
      ...value[selectedDatetime.datetimeString],
      ...exchangesConfig[key],
      key: key,
    }));

  return currentExchanges;
}
