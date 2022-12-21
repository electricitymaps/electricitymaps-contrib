import { PulseLoader } from 'react-spinners';
import { Mode, TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import useBreakdownChartData from './hooks/useBreakdownChartData';
import BreakdownChartTooltip from './tooltips/BreakdownChartTooltip';

interface BreakdownChartProps {
  displayByEmissions: boolean;
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function BreakdownChart({
  displayByEmissions,
  datetimes,
  timeAverage,
}: BreakdownChartProps) {
  const { data, mixMode } = useBreakdownChartData();

  if (!data) {
    return <PulseLoader />;
  }

  const { chartData, valueAxisLabel, layerFill, layerKeys } = data;

  const titleDisplayMode = displayByEmissions ? 'emissions' : 'electricity';
  const titleMixMode = mixMode === Mode.CONSUMPTION ? 'origin' : 'production';
  return (
    <>
      <ChartTitle translationKey={`country-history.${titleDisplayMode}${titleMixMode}`} />
      <AreaGraph
        testId="history-mix-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel={valueAxisLabel}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={false} // Todo: test on mobile https://linear.app/electricitymaps/issue/ELE-1498/test-and-improve-charts-on-mobile
        height="10em"
        isOverlayEnabled={false} // TODO: create overlay https://linear.app/electricitymaps/issue/ELE-1499/implement-chart-overlay-for-unavailable-data
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        tooltip={BreakdownChartTooltip}
        tooltipSize={displayByEmissions ? 'small' : 'large'}
      />
    </>
  );
}

export default BreakdownChart;
