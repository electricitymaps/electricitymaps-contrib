import Accordion from 'components/Accordion';
import Divider from 'features/panels/zone/Divider';
import { IndustryIcon } from 'icons/industryIcon';
import { WindTurbineIcon } from 'icons/windTurbineIcon';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { dataSourcesCollapsedEmission } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import { DataSources } from './DataSources';
import AreaGraph from './elements/AreaGraph';
import { getBadgeText, noop } from './graphUtils';
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

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  const badgeText = getBadgeText(chartData, t);

  if (!hasEnoughDataToDisplay) {
    return <NotEnoughDataMessage title="country-history.carbonintensity" />;
  }
  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        translationKey="country-history.carbonintensity"
        badgeText={badgeText}
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
      <Divider />
      <Accordion
        onOpen={() => {
          trackEvent(TrackEvent.DATA_SOURCES_CLICKED, { chart: 'carbon-chart' });
        }}
        title={t('data-sources.title')}
        isCollapsedAtom={dataSourcesCollapsedEmission}
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
    </RoundedCard>
  );
}

export default CarbonChart;
