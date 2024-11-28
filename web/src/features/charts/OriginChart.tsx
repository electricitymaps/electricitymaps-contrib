import EstimationBadge from 'components/EstimationBadge';
import { MetricRatio } from 'components/MetricRatio';
import { FormattedTime } from 'components/Time';
import { max, sum } from 'd3-array';
import { useAtom, useAtomValue } from 'jotai';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'translation/i18n';
import { ElectricityModeType } from 'types';
import { Charts, TimeAverages } from 'utils/constants';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';
import {
  isConsumptionAtom,
  isHourlyAtom,
  selectedDatetimeIndexAtom,
} from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import AreaGraph, { AreaGraphIndexSelectedAtom } from './elements/AreaGraph';
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

// TODO(cady): fix types to use ElectricityModeType
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

function OriginChart({ displayByEmissions, datetimes, timeAverage }: OriginChartProps) {
  const { data } = useOriginChartData();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const { t } = useTranslation();
  const isHourly = useAtomValue(isHourlyAtom);
  const selectedData = useSelectedData(displayByEmissions);

  // TODO(cady): Clean up; consider controller?
  const [graphIndex] = useAtom(AreaGraphIndexSelectedAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const index = graphIndex ?? selectedDatetime.index;
  const currentDataPointMeta = data?.chartData[index].meta;
  const totalElectricity =
    currentDataPointMeta.totalProduction +
    currentDataPointMeta.totalDischarge +
    (isConsumption ? currentDataPointMeta.totalImport : 0);

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
      <div className="flex flex-col">
        <FormattedTime
          datetime={selectedDatetime.datetime}
          language={i18n.languages[0]}
          timeAverage={timeAverage}
          className="text-xs"
        />
        <MetricRatio
          value={totalElectricity}
          useTotalUnit
          format={isHourly ? formatPower : formatEnergy}
        />
      </div>
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
