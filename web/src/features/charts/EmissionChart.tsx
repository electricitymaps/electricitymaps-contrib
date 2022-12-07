import { PulseLoader } from 'react-spinners';
import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';

import { noop } from './graphUtils';
import { useEmissionChartData } from './hooks/useEmissionChartData';

interface EmissionChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function EmissionChart({ timeAverage, datetimes }: EmissionChartProps) {
  const { data, isLoading, isError } = useEmissionChartData();

  if (isLoading || isError || !data) {
    return <PulseLoader />;
  }

  const { chartData, layerFill, layerKeys } = data;

  return (
    <div className="ml-2">
      <ChartTitle translationKey="country-history.emissions" />
      <AreaGraph
        testId="history-emissions-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="tCO₂eq / min"
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isOverlayEnabled={false}
        datetimes={datetimes}
        isMobile={false}
        selectedTimeAggregate={timeAverage}
        height="8em"
      />
    </div>
  );
}

export default EmissionChart;
