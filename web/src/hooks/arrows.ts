import useGetState from 'api/getState';
import { useAtomValue } from 'jotai';
import { useMemo } from 'react';
import { ExchangeArrowData, StateExchangeData } from 'types';
import { SpatialAggregate } from 'utils/constants';
import { selectedDatetimeStringAtom, spatialAggregateAtom } from 'utils/state/atoms';

import exchangesConfigJSON from '../../config/exchanges.json'; // do something globally
import exchangesToExclude from '../../config/excluded_aggregated_exchanges.json';
// do something globally
interface Arrow {
  capacity?: [number, number];
  lonlat: [number, number];
  rotation: number;
}

interface Arrows {
  [key: string]: Arrow;
}

const exchangesConfig: Arrows = exchangesConfigJSON as unknown as Arrows;

const { exchangesToExcludeZoneView, exchangesToExcludeCountryView } = exchangesToExclude;

/**
 * Determines if the carbon intensity of an exchange should be hidden due to a temporary zone outage.
 * By not passing on carbon intensity, we are able to still show a grey arrow with the power value.
 */
export function shouldHideExchangeIntensity(
  exchange: string,
  zonesWithOutages: string[],
  value: number
) {
  const [zone1, zone2] = exchange.split('->');

  // Check if the exchange is from a zone with an outage and the power is flowing out of the zone
  // and not in. We only want to hide the intensity being exported by the zone.
  return (
    (zonesWithOutages.includes(zone1) && value > 0) ||
    (zonesWithOutages.includes(zone2) && value < 0)
  );
}

export function filterExchanges(
  exchanges: Record<string, StateExchangeData>,
  exclusionArrayZones: string[],
  exclusionArrayCountries: string[]
) {
  const exclusionSetZones = new Set(exclusionArrayZones);
  const exclusionSetCountries = new Set(exclusionArrayCountries);
  const resultZones: Record<string, StateExchangeData> = {};
  const resultCountries: Record<string, StateExchangeData> = {};
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
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const viewMode = useAtomValue(spatialAggregateAtom);
  const { data } = useGetState();

  // Find outages in state data and hide exports from those zones
  const zonesWithOutages = useMemo(() => {
    const zoneData = data?.data?.datetimes?.[selectedDatetimeString]?.z;
    return zoneData
      ? Object.entries(zoneData)
          .filter(([_, value]) => value.o)
          .map(([zone]) => zone)
      : [];
  }, [data, selectedDatetimeString]);

  const exchangesToUse: { [key: string]: StateExchangeData } = useMemo(() => {
    const exchanges = data?.data?.datetimes?.[selectedDatetimeString]?.e;

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
  }, [data, selectedDatetimeString, viewMode]);

  const currentExchanges: ExchangeArrowData[] = useMemo(
    () =>
      Object.entries(exchangesToUse).map(([key, value]) => ({
        co2intensity: shouldHideExchangeIntensity(key, zonesWithOutages, value.f)
          ? Number.NaN
          : value.ci,
        netFlow: value.f,
        ...exchangesConfig[key],
        key,
      })),
    [exchangesToUse, zonesWithOutages]
  );

  return currentExchanges;
}
