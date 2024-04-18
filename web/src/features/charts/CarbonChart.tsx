import { CloudArrowUpIcon } from 'icons/cloudArrowUpIcon';
import { useTranslation } from 'react-i18next';
import { TimeAverages } from 'utils/constants';

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
  const { data, isLoading, isError } = useCarbonChartData();
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
        unit={t('units.g-kwh')}
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
    </GraphCard>
  );
}

export default CarbonChart;
