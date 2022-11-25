import { PulseLoader } from 'react-spinners';
import { TimeAverages } from 'utils/constants';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { useCarbonChartData } from './hooks/useCarbonChartData';

interface CarbonChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function CarbonChart({ datetimes, timeAverage }: CarbonChartProps) {
  const { data, isLoading, isError } = useCarbonChartData();

  if (isLoading || isError || !data) {
    return <PulseLoader />;
  }

  const { chartData, layerFill, layerKeys } = data;

  return (
    <div className="ml-3">
      <AreaGraph
        testId="history-carbon-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="g / kWh"
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={false}
        isOverlayEnabled={false}
        height="8em"
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        selectedZoneTimeIndex={0}
      />
    </div>
  );
}

export default CarbonChart;
