import { max, sum } from 'd3-array';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { useAtomValue } from 'jotai';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import { Charts, TimeRange } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import { isConsumptionAtom, isHourlyAtom } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import EstimationLegend from './elements/EstimationLegend';
import { getGenerationTypeKey, noop } from './graphUtils';
import useOriginChartData from './hooks/useOriginChartData';
import { MissingExchangeDataDisclaimer } from './MissingExchangeData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import ProductionSourceLegendList from './ProductionSourceLegendList';
import { RoundedCard } from './RoundedCard';
import BreakdownChartTooltip from './tooltips/BreakdownChartTooltip';
import { AreaGraphElement } from './types';

interface OriginChartProps {
  displayByEmissions: boolean;
  datetimes: Date[];
  timeRange: TimeRange;
}

// TODO: fix types to use ElectricityModeType
export interface SelectedData {
  select(key: string): void;
  deselect(key: string): void;
  isSelected(key: string): boolean;
  toggle(key: string): void;
  hasSelection(): boolean;
}

const useSelectedData = (displayByEmissions: boolean): SelectedData => {
  const [selectedData, setSelectedData] = useState<Partial<Record<string, boolean>>>({});

  useEffect(() => setSelectedData({}), [displayByEmissions]);

  return useMemo(
    () => ({
      select(key: string) {
        setSelectedData((data) => ({ ...data, [key]: true }));
      },
      deselect(key: string) {
        setSelectedData((data) => ({ ...data, [key]: false }));
      },
      isSelected(key: string): boolean {
        return selectedData[key] ?? false;
      },
      toggle(key: string) {
        if (this.isSelected(key)) {
          this.deselect(key);
        } else {
          this.select(key);
        }
      },
      hasSelection(): boolean {
        return Object.values(selectedData).some(Boolean);
      },
    }),
    [selectedData]
  );
};

function OriginChart({ displayByEmissions, datetimes, timeRange }: OriginChartProps) {
  const { data } = useOriginChartData();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const { t } = useTranslation();
  const isHourly = useAtomValue(isHourlyAtom);
  const selectedData = useSelectedData(displayByEmissions);

  // Call hooks before any conditional returns
  const estimationMethod = data?.chartData?.find((d) => d.meta?.estimationMethod)?.meta
    ?.estimationMethod;
  const estimationText = useGetEstimationTranslation('pill', estimationMethod);

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

  const badge = estimationText ? <EstimationLegend text={estimationText} /> : undefined;
  const isEstimated = Boolean(estimationMethod);

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
        titleText={t(`country-history.${titleDisplayMode}${titleMixMode}.${timeRange}`)}
        badge={badge}
        isEstimated={isEstimated}
        unit={valueAxisLabel}
        id={Charts.ORIGIN_CHART}
      />
      <div className="relative ">
        <AreaGraph
          testId="history-mix-graph"
          isDataInteractive={true}
          selectedData={selectedData}
          data={chartData}
          layerKeys={layerKeys}
          layerFill={layerFill}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          height="10em"
          datetimes={datetimes}
          selectedTimeRange={timeRange}
          tooltip={BreakdownChartTooltip}
          tooltipSize={displayByEmissions ? 'small' : 'large'}
          showEstimationOverlays={true}
          {...(displayByEmissions && { formatTick: formatAxisTick })}
        />
      </div>
      {isConsumptionAndAggregatedResolution && (
        <div
          className="prose my-1 rounded bg-neutral-200 p-2 text-xs leading-snug dark:bg-neutral-800 dark:text-white dark:prose-a:text-white"
          dangerouslySetInnerHTML={{ __html: t('country-panel.exchangesAreMissing') }}
        />
      )}
      <MissingExchangeDataDisclaimer />
      <ProductionSourceLegendList
        sources={getProductionSourcesInChart(chartData)}
        className="py-1.5"
        selectedData={selectedData}
        isDataInteractive={true}
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
