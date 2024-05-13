import Accordion from 'components/Accordion';
import Divider from 'features/panels/zone/Divider';
import { CloudArrowUpIcon } from 'icons/cloudArrowUpIcon';
import { IndustryIcon } from 'icons/industryIcon';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { dataSourcesCollapsedEmission } from 'utils/state/atoms';

import { DataSources } from './bar-breakdown/DataSources';
import { GraphCard } from './bar-breakdown/GraphCard';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { getBadgeText, noop } from './graphUtils';
import { useCarbonChartData } from './hooks/useCarbonChartData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import CarbonChartTooltip from './tooltips/CarbonChartTooltip';

interface CarbonChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function CarbonChart({ datetimes, timeAverage }: CarbonChartProps) {
  const { data, emissionSourceToProductionSource, isLoading, isError } =
    useCarbonChartData();
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
    <GraphCard className="pb-2">
      <ChartTitle
        translationKey="country-history.carbonintensity"
        badgeText={badgeText}
        icon={<CloudArrowUpIcon />}
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
        className="text-md"
        isCollapsedAtom={dataSourcesCollapsedEmission}
      >
        <DataSources
          title={t('data-sources.emission')}
          icon={<IndustryIcon />}
          sourceToProductionSources={emissionSourceToProductionSource}
        />
      </Accordion>
    </GraphCard>
  );
}

export default CarbonChart;
