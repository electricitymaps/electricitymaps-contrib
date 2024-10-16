import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import EstimationBadge from 'components/EstimationBadge';
import { max, sum } from 'd3-array';
import { useAtom, useAtomValue } from 'jotai';
import { Factory, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import {
  dataSourcesCollapsedBreakdownAtom,
  isConsumptionAtom,
  isHourlyAtom,
} from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import { DataSources } from './DataSources';
import AreaGraph from './elements/AreaGraph';
import { getBadgeTextAndIcon, getGenerationTypeKey, noop } from './graphUtils';
import useBreakdownChartData from './hooks/useBreakdownChartData';
import useZoneDataSources from './hooks/useZoneDataSources';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import ProductionSourceLegendList from './ProductionSourceLegendList';
import { RoundedCard } from './RoundedCard';
import BreakdownChartTooltip from './tooltips/BreakdownChartTooltip';
import { AreaGraphElement } from './types';

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
  const { data } = useBreakdownChartData();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const [dataSourcesCollapsedBreakdown, setDataSourcesCollapsedBreakdown] = useAtom(
    dataSourcesCollapsedBreakdownAtom
  );
  const {
    emissionFactorSources,
    powerGenerationSources,
    emissionFactorSourcesToProductionSources,
  } = useZoneDataSources();
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

  const { text, icon } = getBadgeTextAndIcon(chartData, t);

  const badge = <EstimationBadge text={text} Icon={icon} />;

  if (!hasEnoughDataToDisplay) {
    return (
      <NotEnoughDataMessage
        title={`country-history.${titleDisplayMode}${titleMixMode}`}
      />
    );
  }

  return (
    <RoundedCard>
      <ChartTitle
        translationKey={`country-history.${titleDisplayMode}${titleMixMode}`}
        badge={badge}
        unit={valueAxisLabel}
      />
      <div className="relative ">
        <AreaGraph
          testId="history-mix-graph"
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

      <>
        <ProductionSourceLegendList
          sources={getProductionSourcesInChart(chartData)}
          className="py-1.5"
        />
        <HorizontalDivider />
        <Accordion
          onOpen={() => {
            trackEvent(TrackEvent.DATA_SOURCES_CLICKED, {
              chart: displayByEmissions
                ? 'emission-origin-chart'
                : 'electricity-origin-chart',
            });
          }}
          title={t('data-sources.title')}
          className="text-md"
          isCollapsed={dataSourcesCollapsedBreakdown}
          setState={setDataSourcesCollapsedBreakdown}
        >
          <DataSources
            title={t('data-sources.power')}
            icon={<Zap size={16} />}
            sources={powerGenerationSources}
          />
          <DataSources
            title={t('data-sources.emission')}
            icon={<Factory size={16} />}
            sources={emissionFactorSources}
            emissionFactorSourcesToProductionSources={
              emissionFactorSourcesToProductionSources
            }
          />
        </Accordion>
      </>
    </RoundedCard>
  );
}

export default BreakdownChart;

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
