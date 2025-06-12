import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { Charts, TimeRange } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import { isHourlyAtom } from 'utils/state/atoms';

import { ChartSubtitle, ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { EstimationLegend } from './elements/EstimationMarkers';
import { noop } from './graphUtils';
import { useEmissionChartData } from './hooks/useEmissionChartData';
import { useEstimationData } from './hooks/useEstimationData';
import { RoundedCard } from './RoundedCard';
import EmissionChartTooltip from './tooltips/EmissionChartTooltip';

interface EmissionChartProps {
  datetimes: Date[];
  timeRange: TimeRange;
}

function EmissionChart({ timeRange, datetimes }: EmissionChartProps) {
  const { data, isLoading, isError } = useEmissionChartData();
  const isHourly = useAtomValue(isHourlyAtom);
  const { estimated, estimationMethod, someEstimated } = useEstimationData(
    data?.chartData
  );

  const { t } = useTranslation();
  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  const valueAxisLabel = 'gCO₂eq';
  const maxEmissions = Math.max(...chartData.map((o) => o.layerData.emissions));
  const formatAxisTick = (t: number) => formatCo2({ value: t, total: maxEmissions });

  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        titleText={t(`country-history.emissions.${timeRange}`)}
        unit={someEstimated ? undefined : valueAxisLabel}
        id={Charts.EMISSION_CHART}
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
      />
      {someEstimated && (
        <EstimationLegend
          isAggregated={!isHourly}
          estimationMethod={estimationMethod}
          valueAxisLabel={valueAxisLabel}
        />
      )}
      <AreaGraph
        testId="history-emissions-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        datetimes={datetimes}
        estimated={estimated}
        selectedTimeRange={timeRange}
        height="8em"
        tooltip={EmissionChartTooltip}
        formatTick={formatAxisTick}
      />
    </RoundedCard>
  );
}

export default EmissionChart;
