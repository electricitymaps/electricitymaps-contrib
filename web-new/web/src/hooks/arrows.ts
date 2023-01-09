/* eslint-disable unicorn/no-array-reduce */
import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { ExchangeArrowData, ExchangeResponse } from 'types';
import { TimeAverages, ToggleOptions } from 'utils/constants';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import exchangesConfigJSON from '../../config/exchanges.json'; // do something globally
import exchangesToExclude from '../../config/excludedAggregatedExchanges.json'; // do something globally

// TODO: set up proper typed method for retrieving config files.
const exchangesConfig: Record<string, any> = exchangesConfigJSON;

export function useExchangeArrowsData(): ExchangeArrowData[] {
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [aggregateToggle] = useAtom(spatialAggregateAtom);
  const { data, isError, isLoading } = useGetState();
  const [mode] = useAtom(productionConsumptionAtom);
  const isConsumption = mode === 'consumption';
  const isHourly = timeAverage === TimeAverages.HOURLY;

  const exchangesToUse: { [key: string]: ExchangeResponse } = useMemo(() => {
    const exchanges = data?.data.exchanges;

    if (!exchanges) {
      return [];
    }

    const zoneViewExchanges = Object.keys(exchanges)
      .filter((key) => !exchangesToExclude.exchangesToExcludeZoneView.includes(key))
      .reduce((current, key) => {
        return Object.assign(current, { [key]: exchanges[key] });
      }, {});

    const countryViewExchanges = Object.keys(exchanges)
      .filter((key) => !exchangesToExclude.exchangesToExcludeCountryView.includes(key))
      .reduce((current, key) => {
        return Object.assign(current, { [key]: exchanges[key] });
      }, {});

    return aggregateToggle === ToggleOptions.ON
      ? countryViewExchanges
      : zoneViewExchanges;
  }, [aggregateToggle, data]);

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
