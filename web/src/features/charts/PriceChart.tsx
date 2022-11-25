import { PulseLoader } from 'react-spinners';
import { TimeAverages } from 'utils/constants';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { usePriceChartData } from './hooks/usePriceChartData';

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
    <div className="ml-3">
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
        selectedZoneTimeIndex={0}
        isOverlayEnabled={false}
      />
    </div>
  );
}

export default PriceChart;
