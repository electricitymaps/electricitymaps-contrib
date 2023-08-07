import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { useNetExchangeChartData } from './hooks/useNetExchangeChartData';
import NetExchangeChartTooltip from './tooltips/NetExchangeChartTooltip';
import { useAtom } from 'jotai';
import { productionConsumptionAtom } from 'utils/state/atoms';

interface NetExchangeChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function NetExchangeChart({ datetimes, timeAverage }: NetExchangeChartProps) {
  const { data, isLoading, isError } = useNetExchangeChartData();

  if (isLoading || isError || !data) {
    return null;
  }
  const { chartData } = data;
  const { layerFill, layerKeys, layerStroke, valueAxisLabel, markerFill } = data;

  if (!chartData[0]?.layerData?.netExchange) {
    return null;
  }
  const [productionConsumption] = useAtom(productionConsumptionAtom);
  return productionConsumption === 'consumption' ? (
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
          height="10em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={NetExchangeChartTooltip}
        />
      </div>
    </>
  ) : undefined;
}

export default NetExchangeChart;
