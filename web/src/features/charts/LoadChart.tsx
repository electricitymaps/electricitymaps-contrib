import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { Charts, TimeRange } from 'utils/constants';
import { isHourlyAtom } from 'utils/state/atoms';

import { ChartSubtitle, ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { EstimationLegend } from './elements/EstimationMarkers';
import { noop } from './graphUtils';
import { useEstimationData } from './hooks/useEstimationData';
import { useLoadChartData } from './hooks/useLoadChartData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import { RoundedCard } from './RoundedCard';
import LoadChartTooltip from './tooltips/LoadChartTooltip';

interface LoadChartProps {
  datetimes: Date[];
  timeRange: TimeRange;
}

function LoadChart({ datetimes, timeRange }: LoadChartProps) {
  const { data, isLoading, isError } = useLoadChartData();
  const { t } = useTranslation();
  const isHourly = useAtomValue(isHourlyAtom);
  const { estimated, estimationMethod, someEstimated } = useEstimationData(
    data?.chartData
  );

  if (isLoading || isError || !data) {
    return null;
  }
  const { chartData } = data;
  const { layerFill, layerKeys, layerStroke, valueAxisLabel, markerFill } = data;

  if (!Number.isFinite(chartData[0]?.layerData?.load)) {
    return null;
  }

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  if (!hasEnoughDataToDisplay) {
    return (
      <NotEnoughDataMessage
        id={Charts.ELECTRICITY_LOAD_CHART}
        title="country-history.electricityload"
      />
    );
  }

  return (
    <RoundedCard>
      <ChartTitle
        titleText={t(($) => $['country-history'].electricityLoad[timeRange])}
        unit={someEstimated ? undefined : valueAxisLabel}
        id={Charts.ELECTRICITY_LOAD_CHART}
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
      />
      <div className="relative">
        {someEstimated && (
          <EstimationLegend
            isAggregated={!isHourly}
            estimationMethod={estimationMethod}
            valueAxisLabel={valueAxisLabel}
          />
        )}
        <AreaGraph
          testId="history-load-graph"
          data={chartData}
          layerKeys={layerKeys}
          layerStroke={layerStroke}
          layerFill={layerFill}
          markerFill={markerFill}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          height="6em"
          datetimes={datetimes}
          estimated={estimated}
          selectedTimeRange={timeRange}
          tooltip={LoadChartTooltip}
        />
      </div>
    </RoundedCard>
  );
}

export default LoadChart;
