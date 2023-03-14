import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';

import { noop } from './graphUtils';
import { useEmissionChartData } from './hooks/useEmissionChartData';
import EmissionChartTooltip from './tooltips/EmissionChartTooltip';

interface EmissionChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function EmissionChart({ timeAverage, datetimes }: EmissionChartProps) {
  const { data, isLoading, isError } = useEmissionChartData();

  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  return (
    <>
      <ChartTitle translationKey="country-history.emissions" />
      <AreaGraph
        testId="history-emissions-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="tCO₂eq / min"
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        datetimes={datetimes}
        isMobile={false}
        selectedTimeAggregate={timeAverage}
        height="8em"
        tooltip={EmissionChartTooltip}
      />
    </>
  );
}

export default EmissionChart;
