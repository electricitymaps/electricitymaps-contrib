import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { useNetExchangeChartData } from './hooks/useNetExchangeChartData';
import PriceChartTooltip from './tooltips/PriceChartTooltip';

interface NetExchangeChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function NetExchangeChart({ datetimes, timeAverage }: NetExchangeChartProps) {
  const { data, isLoading, isError } = useNetExchangeChartData();
  console.log(data);

  if (isLoading || isError || !data) {
    return null;
  }
  const { chartData } = data;
  const { layerFill, layerKeys, layerStroke, valueAxisLabel, markerFill } = data;

  if (!chartData[0]?.layerData?.netExchange) {
    return null;
  }
  return (
    <>
      <ChartTitle translationKey="country-history.netExchange" />
      <div className="relative">
        <AreaGraph
          testId="history-exchange-graph"
          data={chartData}
          layerKeys={layerKeys}
          layerStroke={layerStroke}
          layerFill={layerFill}
          markerFill={markerFill}
          valueAxisLabel={valueAxisLabel}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          isMobile={false}
          height="6em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={PriceChartTooltip} // TODO: Replace with NetExchangeChartTooltip
        />
      </div>
    </>
  );
}

export default NetExchangeChart;
