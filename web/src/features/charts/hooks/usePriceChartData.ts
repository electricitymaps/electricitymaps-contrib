import useGetState from 'api/getState';
import useGetZone from 'api/getZone';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { usePriceColorScale } from 'hooks/theme';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';

import { convertPrice } from '../bar-breakdown/utils';
import { AreaGraphElement } from '../types';

export function getPriceColorScale(data: AreaGraphElement[]) {
  const prices = Object.values(data).map((d) => d.layerData.price);
  const priceMaxValue = d3Max<number>(prices) ?? 0;
  const priceMinValue = d3Min<number>(prices) ?? 0;

  return scaleLinear<string>()
    .domain([priceMinValue, 0, priceMaxValue])
    .range(['gray', 'lightgray', '#616161']);
}

export function usePriceChartData() {
  const { data: zoneDetails, isLoading, isError } = useGetZone();
  const { zoneId } = useParams<RouteParameters>();
  // Detect if we should use the map's price color scale
  const mapPriceColorScale = usePriceColorScale();
  const { data } = useGetState();
  if (data?.datetimes == null || zoneId == null) {
    return { isLoading, isError };
  }
  const shouldUseMapColorScale = Object.values(data?.datetimes)?.some(
    (value) => value?.z[zoneId].pr != null
  );

  if (isLoading || isError || !zoneDetails) {
    return { isLoading, isError };
  }

  const firstZoneState = Object.values(zoneDetails.zoneStates)[0].price;
  // We assume that if the first element has price disabled, all of them do
  const priceDisabledReason = firstZoneState?.disabledReason;

  const { currency, unit } = convertPrice(
    firstZoneState?.value,
    firstZoneState?.currency
  );

  const chartData = Object.entries(zoneDetails.zoneStates).map(
    ([datetimeString, value]) => ({
      datetime: new Date(datetimeString),
      layerData: {
        price:
          convertPrice(value.price?.value, value.price?.currency).value ?? Number.NaN,
      },
      meta: value,
    })
  );

  const futurePrice = zoneDetails.futurePrice;

  const currencySymbol: string = getSymbolFromCurrency(currency?.toUpperCase());
  const valueAxisLabel = `${currencySymbol || '?'} / ${unit}`;

  const priceColorScale = shouldUseMapColorScale
    ? mapPriceColorScale
    : getPriceColorScale(chartData);
  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    priceColorScale(d.data.layerData[key]);

  const markerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    priceColorScale(d.data.layerData[key]);

  const layerKeys = ['price'];

  const result = {
    chartData,
    layerKeys,
    layerFill,
    markerFill,
    valueAxisLabel,
    layerStroke: undefined,
    priceDisabledReason,
    futurePrice,
  };

  return { data: result, isLoading, isError };
}
