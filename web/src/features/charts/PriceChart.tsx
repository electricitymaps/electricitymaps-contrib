import { PulseLoader } from 'react-spinners';
import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { usePriceChartData } from './hooks/usePriceChartData';
import PriceChartTooltip from './tooltips/PriceChartTooltip';

interface PriceChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function PriceChart({ datetimes, timeAverage }: PriceChartProps) {
  // TODO: incorporate https://github.com/electricitymaps/electricitymaps-contrib/pull/4749
  const { data, isLoading, isError } = usePriceChartData();

  if (isLoading || isError || !data) {
    return <PulseLoader />;
  }

  const { chartData, layerFill, layerKeys, layerStroke, valueAxisLabel, markerFill } =
    data;

  return (
    <div className="ml-4">
      <ChartTitle translationKey="country-history.electricityprices" />
      <AreaGraph
        testId="history-prices-graph"
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
        isOverlayEnabled={false}
        tooltip={PriceChartTooltip}
      />
    </div>
  );
}

export default PriceChart;
