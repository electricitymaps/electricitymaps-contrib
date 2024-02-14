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

export function filterExchanges(
  exchanges: Record<string, ExchangeResponse>,
  exclusionArrayZones: string[],
  exclusionArrayCountries: string[]
) {
  const exclusionSetZones = new Set(exclusionArrayZones);
  const exclusionSetCountries = new Set(exclusionArrayCountries);
  const resultZones: Record<string, ExchangeResponse> = {};
  const resultCountries: Record<string, ExchangeResponse> = {};
  // Loop through the exchanges and assign them to the correct result object
  for (const [key, value] of Object.entries(exchanges)) {
    if (exclusionSetCountries.has(key)) {
      resultZones[key] = value;
    } else if (exclusionSetZones.has(key)) {
      resultCountries[key] = value;
    } else {
      resultZones[key] = value;
      resultCountries[key] = value;
    }
  }

  return [resultZones, resultCountries];
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

    const [zoneViewExchanges, countryViewExchanges] = filterExchanges(
      exchanges,
      exchangesToExcludeZoneView,
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
