import EstimationBadge from 'components/EstimationBadge';
import { useTranslation } from 'react-i18next';
import { Charts, TimeAverages } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';

import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { getBadgeTextAndIcon, noop } from './graphUtils';
import { useEmissionChartData } from './hooks/useEmissionChartData';
import { RoundedCard } from './RoundedCard';
import EmissionChartTooltip from './tooltips/EmissionChartTooltip';

interface EmissionChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function EmissionChart({ timeAverage, datetimes }: EmissionChartProps) {
  const { data, isLoading, isError } = useEmissionChartData();

  const { t } = useTranslation();
  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  const maxEmissions = Math.max(...chartData.map((o) => o.layerData.emissions));
  const formatAxisTick = (t: number) => formatCo2({ value: t, total: maxEmissions });

  const { text, icon, allEstimated } = getBadgeTextAndIcon(chartData, t);
  const badge = allEstimated ? <EstimationBadge text={text} Icon={icon} /> : undefined;

  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        titleText={t(`country-history.emissions.${timeAverage}`)}
        badge={badge}
        unit={'CO₂eq'}
        id={Charts.EMISSION_CHART}
      />
      <AreaGraph
        testId="history-emissions-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        datetimes={datetimes}
        isMobile={false}
        selectedTimeAggregate={timeAverage}
        height="8em"
        tooltip={EmissionChartTooltip}
        formatTick={formatAxisTick}
      />
    </RoundedCard>
  );
}

export default EmissionChart;
