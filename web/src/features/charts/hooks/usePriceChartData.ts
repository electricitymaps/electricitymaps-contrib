import useGetZone from 'api/getZone';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { AreaGraphElement } from '../types';

export function getFills(data: AreaGraphElement[]) {
  const priceMaxValue =
    d3Max<number>(Object.values(data).map((d) => d.layerData.price || 0)) ?? 0;
  const priceMinValue =
    d3Min<number>(Object.values(data).map((d) => d.layerData.price || 0)) ?? 0;

  const priceColorScale = scaleLinear<string>()
    .domain([priceMinValue, 0, priceMaxValue])
    .range(['brown', 'lightgray', '#616161']);

  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    priceColorScale(d.data.layerData[key]);

  const markerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    priceColorScale(d.data.layerData[key]);

  return { layerFill, markerFill };
}

export function usePriceChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();

  if (isLoading || isError) {
    return { isLoading, isError };
  }

  // We assume that if the first element has price disabled, all of them do
  const priceDisabledReason = Object.values(zoneData.zoneStates)[0].price?.disabledReason;

  const chartData: AreaGraphElement[] = [];

  for (const [datetimeString, value] of Object.entries(zoneData.zoneStates)) {
    const datetime = new Date(datetimeString);
    chartData.push({
      datetime,
      layerData: {
        price: value.price?.value ?? Number.NaN,
      },
      meta: value,
    });
  }

  const currencySymbol: string = getSymbolFromCurrency(
    Object.values(zoneData.zoneStates)[0].price?.currency // Every price has the same currency
  );
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const { layerFill, markerFill } = getFills(chartData);

  const layerKeys = ['price'];

  const result = {
    chartData,
    layerKeys,
    layerFill,
    markerFill,
    valueAxisLabel,
    layerStroke: undefined,
    priceDisabledReason,
  };

  return { data: result, isLoading, isError };
}
