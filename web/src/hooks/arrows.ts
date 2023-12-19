import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { ExchangeArrowData, StateExchangeData } from 'types';
import { SpatialAggregate } from 'utils/constants';
import { selectedDatetimeIndexAtom, spatialAggregateAtom } from 'utils/state/atoms';

import exchangesConfigJSON from '../../config/exchanges.json'; // do something globally
import exchangesToExclude from '../../config/excluded_aggregated_exchanges.json'; // do something globally

const exchangesConfig: Record<string, any> = exchangesConfigJSON;

export function useExchangeArrowsData(): ExchangeArrowData[] {
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [viewMode] = useAtom(spatialAggregateAtom);
  const { data } = useGetState();

  const exchangesToUse: { [key: string]: StateExchangeData } = useMemo(() => {
    const exchanges = data?.data?.datetimes?.[selectedDatetime?.datetimeString]?.e;

    const exchangesToExcludeZoneViewSet = new Set(
      exchangesToExclude.exchangesToExcludeZoneView
    );
    const exchangesToExcludeCountryViewSet = new Set(
      exchangesToExclude.exchangesToExcludeCountryView
    );

    const zoneViewExchanges: { [key: string]: StateExchangeData } = {};
    const countryViewExchanges: { [key: string]: StateExchangeData } = {};

    for (const key of Object.keys(exchanges ?? {})) {
      if (!exchangesToExcludeZoneViewSet.has(key)) {
        zoneViewExchanges[key] = exchanges?.[key] ?? {};
      }
      if (!exchangesToExcludeCountryViewSet.has(key)) {
        countryViewExchanges[key] = exchanges?.[key] ?? {};
      }
    }

    return viewMode === SpatialAggregate.COUNTRY
      ? countryViewExchanges
      : zoneViewExchanges;
  }, [data, selectedDatetime, viewMode]);

  const currentExchanges: ExchangeArrowData[] = useMemo(() => {
    return Object.entries(exchangesToUse).map(([key, value]) => ({
      ...value,
      ...exchangesConfig[key],
      key,
    }));
  }, [exchangesToUse]);

  return currentExchanges;
}
