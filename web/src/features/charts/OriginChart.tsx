import EstimationBadge from 'components/EstimationBadge';
import { max, sum } from 'd3-array';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import { Charts, TimeAverages } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import { isConsumptionAtom, isHourlyAtom } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { getBadgeTextAndIcon, getGenerationTypeKey, noop } from './graphUtils';
import useOriginChartData from './hooks/useOriginChartData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import ProductionSourceLegendList from './ProductionSourceLegendList';
import { RoundedCard } from './RoundedCard';
import BreakdownChartTooltip from './tooltips/BreakdownChartTooltip';
import { AreaGraphElement } from './types';

interface OriginChartProps {
  displayByEmissions: boolean;
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function OriginChart({ displayByEmissions, datetimes, timeAverage }: OriginChartProps) {
  const { data } = useOriginChartData();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const { t } = useTranslation();
  const isHourly = useAtomValue(isHourlyAtom);

  if (!data) {
    return null;
  }

  const isConsumptionAndAggregatedResolution = isConsumption && !isHourly;

  const { chartData, valueAxisLabel, layerFill, layerKeys } = data;

  // Find highest daily emissions to show correct unit on chart
  const maxEmissions = max(chartData.map((day) => sum(Object.values(day.layerData))));

  const formatAxisTick = (t: number) => formatCo2({ value: t, total: maxEmissions });

  const titleDisplayMode = displayByEmissions ? 'emissions' : 'electricity';
  const titleMixMode = isConsumption ? 'origin' : 'production';

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  const { text, icon, allEstimated } = getBadgeTextAndIcon(chartData, t);
  const badge = allEstimated ? <EstimationBadge text={text} Icon={icon} /> : undefined;

  if (!hasEnoughDataToDisplay) {
    return (
      <NotEnoughDataMessage
        id={Charts.ORIGIN_CHART}
        title={`country-history.${titleDisplayMode}${titleMixMode}`}
      />
    );
  }

  return (
    <RoundedCard>
      <ChartTitle
        titleText={t(`country-history.${titleDisplayMode}${titleMixMode}.${timeAverage}`)}
        badge={badge}
        isEstimated={Boolean(text)}
        unit={valueAxisLabel}
        id={Charts.ORIGIN_CHART}
      />
      <div className="relative ">
        <AreaGraph
          testId="history-mix-graph"
          showHoverHighlight={true}
          data={chartData}
          layerKeys={layerKeys}
          layerFill={layerFill}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          isMobile={false} // Todo: test on mobile https://linear.app/electricitymaps/issue/ELE-1498/test-and-improve-charts-on-mobile
          height="10em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={BreakdownChartTooltip}
          tooltipSize={displayByEmissions ? 'small' : 'large'}
          {...(displayByEmissions && { formatTick: formatAxisTick })}
        />
      </div>
      {isConsumptionAndAggregatedResolution && (
        <div
          className="prose my-1 rounded bg-gray-200 p-2 text-sm leading-snug dark:bg-gray-800 dark:text-white dark:prose-a:text-white"
          dangerouslySetInnerHTML={{ __html: t('country-panel.exchangesAreMissing') }}
        />
      )}
      <ProductionSourceLegendList
        sources={getProductionSourcesInChart(chartData)}
        className="py-1.5"
      />
    </RoundedCard>
  );
}

export default OriginChart;

function getProductionSourcesInChart(chartData: AreaGraphElement[]) {
  const productionSources = new Set<ElectricityModeType>();

  for (const period of chartData) {
    for (const entry of Object.entries(period.layerData)) {
      const [source, value] = entry;
      if (value && getGenerationTypeKey(source)) {
        productionSources.add(source as ElectricityModeType);
      }
    }
  }

  return [...productionSources];
}
