import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { Charts, TimeRange } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import {
  displayByEmissionsAtom,
  isFineGranularityAtom,
  productionConsumptionAtom,
} from 'utils/state/atoms';

import { ChartSubtitle, ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { EstimationLegend } from './elements/EstimationMarkers';
import { noop } from './graphUtils';
import { useEstimationData } from './hooks/useEstimationData';
import { useNetExchangeChartData } from './hooks/useNetExchangeChartData';
import { MissingExchangeDataDisclaimer } from './MissingExchangeData';
import { RoundedCard } from './RoundedCard';
import NetExchangeChartTooltip from './tooltips/NetExchangeChartTooltip';

interface NetExchangeChartProps {
  datetimes: Date[];
  timeRange: TimeRange;
}

function NetExchangeChart({ datetimes, timeRange }: NetExchangeChartProps) {
  const { data, isLoading, isError } = useNetExchangeChartData();
  const productionConsumption = useAtomValue(productionConsumptionAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const isFineGranularity = useAtomValue(isFineGranularityAtom);
  const { t } = useTranslation();
  const { estimated, estimationMethod, someEstimated } = useEstimationData(
    data?.chartData
  );
  if (productionConsumption === 'production') {
    return null;
  }

  if (isLoading || isError || !data) {
    return null;
  }
  const { chartData } = data;
  const { layerFill, layerKeys, layerStroke, valueAxisLabel, markerFill } = data;

  // find the absolute max value to format the axis
  const maxEmissions = Math.max(
    ...chartData.map((o) => Math.abs(o.layerData.netExchange))
  );
  const formatAxisTick = (t: number) =>
    displayByEmissions ? formatCo2({ value: t, total: maxEmissions }) : t.toString();

  if (!chartData[0]?.layerData?.netExchange) {
    return null;
  }

  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        titleText={t(`country-history.netExchange.${timeRange}`)}
        unit={someEstimated ? undefined : valueAxisLabel}
        id={Charts.ELECTRTICITY_FLOW_CHART}
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
      />
      <div className="relative">
        {someEstimated && (
          <EstimationLegend
            isAggregated={!isFineGranularity}
            estimationMethod={estimationMethod}
            valueAxisLabel={valueAxisLabel}
          />
        )}
        <AreaGraph
          testId="history-exchange-graph"
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
          tooltip={NetExchangeChartTooltip}
          formatTick={formatAxisTick}
        />
        <MissingExchangeDataDisclaimer />
      </div>
    </RoundedCard>
  );
}

export default NetExchangeChart;
