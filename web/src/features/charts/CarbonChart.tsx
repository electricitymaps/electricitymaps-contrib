import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { useCarbonChartData } from './hooks/useCarbonChartData';
import CarbonChartTooltip from './tooltips/CarbonChartTooltip';

interface CarbonChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function CarbonChart({ datetimes, timeAverage }: CarbonChartProps) {
  const { data, isLoading, isError } = useCarbonChartData();

  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  return (
    <>
      <ChartTitle translationKey="country-history.carbonintensity" />
      <AreaGraph
        testId="details-carbon-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="g / kWh"
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={false}
        height="8em"
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        tooltip={CarbonChartTooltip}
      />
    </>
  );
}

export default CarbonChart;
