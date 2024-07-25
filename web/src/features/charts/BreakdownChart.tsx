import Accordion from 'components/Accordion';
import { max, sum } from 'd3-array';
import Divider from 'features/panels/zone/Divider';
import { IndustryIcon } from 'icons/industryIcon';
import { WindTurbineIcon } from 'icons/windTurbineIcon';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import trackEvent from 'utils/analytics';
import { Mode, TimeAverages, TrackEvent } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import { dataSourcesCollapsedBreakdown, isHourlyAtom } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import { DataSources } from './DataSources';
import { DisabledMessage } from './DisabledMessage';
import AreaGraph from './elements/AreaGraph';
import { getBadgeText, getGenerationTypeKey, noop } from './graphUtils';
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
  const { data, mixMode } = useBreakdownChartData();
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

  const isBreakdownGraphOverlayEnabled = mixMode === Mode.CONSUMPTION && !isHourly;

  const { chartData, valueAxisLabel, layerFill, layerKeys } = data;

  // Find highest daily emissions to show correct unit on chart
  const maxEmissions = max(chartData.map((day) => sum(Object.values(day.layerData))));

  const formatAxisTick = (t: number) => formatCo2(t, maxEmissions);

  const titleDisplayMode = displayByEmissions ? 'emissions' : 'electricity';
  const titleMixMode = mixMode === Mode.CONSUMPTION ? 'origin' : 'production';

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  const badgeText = getBadgeText(chartData, t);

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
        badgeText={isBreakdownGraphOverlayEnabled ? undefined : badgeText}
        unit={valueAxisLabel}
      />
      <div className="relative ">
        {isBreakdownGraphOverlayEnabled && (
          <DisabledMessage message={t(`country-panel.disabledBreakdownChartReason`)} />
        )}

        <AreaGraph
          testId="history-mix-graph"
          data={chartData}
          layerKeys={layerKeys}
          layerFill={layerFill}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          isMobile={false} // Todo: test on mobile https://linear.app/electricitymaps/issue/ELE-1498/test-and-improve-charts-on-mobile
          height="10em"
          isDisabled={isBreakdownGraphOverlayEnabled}
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={BreakdownChartTooltip}
          tooltipSize={displayByEmissions ? 'small' : 'large'}
          {...(displayByEmissions && { formatTick: formatAxisTick })}
        />
      </div>
      {isBreakdownGraphOverlayEnabled && (
        <div
          className="prose my-1 rounded bg-gray-200 p-2 text-sm leading-snug dark:bg-gray-800 dark:text-white dark:prose-a:text-white"
          dangerouslySetInnerHTML={{ __html: t('country-panel.exchangesAreMissing') }}
        />
      )}
      {!isBreakdownGraphOverlayEnabled && (
        <>
          <ProductionSourceLegendList
            sources={getProductionSourcesInChart(chartData)}
            className="py-1.5"
          />
          <Divider />
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
            isCollapsedAtom={dataSourcesCollapsedBreakdown}
          >
            <DataSources
              title={t('data-sources.power')}
              icon={<WindTurbineIcon />}
              sources={powerGenerationSources}
            />
            <DataSources
              title={t('data-sources.emission')}
              icon={<IndustryIcon />}
              sources={emissionFactorSources}
              emissionFactorSourcesToProductionSources={
                emissionFactorSourcesToProductionSources
              }
            />
          </Accordion>
        </>
      )}
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
