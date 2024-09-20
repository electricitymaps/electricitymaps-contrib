import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import EstimationBadge from 'components/EstimationBadge';
import HorizontalColorbar from 'components/legend/ColorBar';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { Factory, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { dataSourcesCollapsedEmissionAtom } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import { DataSources } from './DataSources';
import AreaGraph from './elements/AreaGraph';
import { getBadgeTextAndIcon, noop } from './graphUtils';
import { useCarbonChartData } from './hooks/useCarbonChartData';
import useZoneDataSources from './hooks/useZoneDataSources';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import { RoundedCard } from './RoundedCard';
import CarbonChartTooltip from './tooltips/CarbonChartTooltip';

interface CarbonChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function CarbonChart({ datetimes, timeAverage }: CarbonChartProps) {
  const { data, isLoading, isError } = useCarbonChartData();
  const [dataSourcesCollapsedEmission, setDataSourcesCollapsedEmission] = useAtom(
    dataSourcesCollapsedEmissionAtom
  );
  const {
    emissionFactorSources,
    powerGenerationSources,
    emissionFactorSourcesToProductionSources,
  } = useZoneDataSources();
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();

  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  const { text, icon } = getBadgeTextAndIcon(chartData, t);
  const badge = <EstimationBadge text={text} Icon={icon} />;

  if (!hasEnoughDataToDisplay) {
    return <NotEnoughDataMessage title="country-history.carbonintensity" />;
  }
  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        translationKey="country-history.carbonintensity"
        badge={badge}
        unit={'gCO₂eq / kWh'}
      />
      <AreaGraph
        testId="details-carbon-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={false}
        height="8em"
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        tooltip={CarbonChartTooltip}
      />
      <div className="pb-1 pt-2">
        <HorizontalColorbar colorScale={co2ColorScale} ticksCount={6} id={'co2'} />
      </div>
      <HorizontalDivider />
      <Accordion
        onOpen={() => {
          trackEvent(TrackEvent.DATA_SOURCES_CLICKED, { chart: 'carbon-chart' });
        }}
        title={t('data-sources.title')}
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

export default CarbonChart;
