import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { useNetExchangeChartData } from './hooks/useNetExchangeChartData';
import NetExchangeChartTooltip from './tooltips/NetExchangeChartTooltip';
import { useAtom } from 'jotai';
import { displayByEmissionsAtom, productionConsumptionAtom } from 'utils/state/atoms';
import { formatCo2 } from 'utils/formatting';

interface NetExchangeChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function NetExchangeChart({ datetimes, timeAverage }: NetExchangeChartProps) {
  const { data, isLoading, isError } = useNetExchangeChartData();
  const [productionConsumption] = useAtom(productionConsumptionAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  if (productionConsumption === 'production') {
    return null;
  }

  if (isLoading || isError || !data) {
    return null;
  }
  const { chartData } = data;
  const { layerFill, layerKeys, layerStroke, valueAxisLabel, markerFill } = data;

  const maxEmissions = Math.max(...chartData.map((o) => o.layerData.netExchange));
  const formatAxisTick = (t: number) =>
    displayByEmissions ? formatCo2(t, maxEmissions) : t.toString();

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
          height="10em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={NetExchangeChartTooltip}
          formatTick={formatAxisTick}
        />
      </div>
    </>
  );
}

export default NetExchangeChart;
