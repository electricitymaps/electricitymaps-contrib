import useGetZone from 'api/getZone';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { ZoneDetail } from 'types';
import { AreaGraphElement } from '../types';

export function usePriceChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();

  if (isLoading || isError) {
    return { isLoading, isError };
  }

  const chartData: AreaGraphElement[] = [];

  for (const [datetimeString, value] of Object.entries(zoneData.zoneStates)) {
    const datetime = new Date(datetimeString);
    if (!value.price?.value) {
      // TODO: should there still be a point in the graph?
      continue;
    }
    chartData.push({
      datetime,
      layerData: {
        price: value.price?.value,
      },
      meta: {},
    });
  }

  const currencySymbol: string = getSymbolFromCurrency(
    Object.values(zoneData.zoneStates)[0].price?.currency // Every price has the same currency
  );
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const priceMaxValue =
    d3Max<number>(
      Object.values(zoneData.zoneStates).map((d: ZoneDetail) => d.price?.value || 0)
    ) || 0;
  const priceMinValue =
    d3Min<number>(
      Object.values(zoneData.zoneStates).map((d: ZoneDetail) => d.price?.value || 0)
    ) || 0;

  const priceColorScale = scaleLinear<string>()
    .domain([priceMinValue, 0, priceMaxValue])
    .range(['brown', 'lightgray', '#616161']);

  const layerKeys = ['price'];

  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    priceColorScale(d.data.layerData[key]);

  const markerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    priceColorScale(d.data.layerData[key]);

  const result = {
    chartData,
    layerKeys,
    layerFill,
    markerFill,
    valueAxisLabel,
    layerStroke: undefined,
  };

  return { data: result, isLoading, isError };
}
