import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import EstimationBadge from 'components/EstimationBadge';
import { useAtom } from 'jotai';
import { Factory, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { formatCo2 } from 'utils/formatting';
import { dataSourcesCollapsedEmissionAtom } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import { DataSources } from './DataSources';
import AreaGraph from './elements/AreaGraph';
import { getBadgeTextAndIcon, noop } from './graphUtils';
import { useEmissionChartData } from './hooks/useEmissionChartData';
import useZoneDataSources from './hooks/useZoneDataSources';
import { RoundedCard } from './RoundedCard';
import EmissionChartTooltip from './tooltips/EmissionChartTooltip';

interface EmissionChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function EmissionChart({ timeAverage, datetimes }: EmissionChartProps) {
  const { data, isLoading, isError } = useEmissionChartData();
  const [dataSourcesCollapsedEmission, setDataSourcesCollapsedEmission] = useAtom(
    dataSourcesCollapsedEmissionAtom
  );
  const {
    emissionFactorSources,
    powerGenerationSources,
    emissionFactorSourcesToProductionSources,
  } = useZoneDataSources();
  const { t } = useTranslation();
  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  const maxEmissions = Math.max(...chartData.map((o) => o.layerData.emissions));
  const formatAxisTick = (t: number) => formatCo2({ value: t, total: maxEmissions });

  const { text, icon } = getBadgeTextAndIcon(chartData, t);
  const badge = <EstimationBadge text={text} Icon={icon} />;

  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        translationKey="country-history.emissions"
        badge={badge}
        unit={'CO₂eq'}
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
      <HorizontalDivider />
      <Accordion
        onOpen={() => {
          trackEvent(TrackEvent.DATA_SOURCES_CLICKED, { chart: 'emission-chart' });
        }}
        title={t('data-sources.title')}
        className="text-md"
        isCollapsed={dataSourcesCollapsedEmission}
        setState={setDataSourcesCollapsedEmission}
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
    </RoundedCard>
  );
}

export default EmissionChart;
