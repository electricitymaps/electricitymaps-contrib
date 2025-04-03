import EstimationBadge from 'components/EstimationBadge';
import HorizontalColorbar from 'components/legend/ColorBar';
import { useCo2ColorScale } from 'hooks/theme';
import { useTranslation } from 'react-i18next';
import { Charts, TimeRange } from 'utils/constants';

import { ChartSubtitle, ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { getBadgeTextAndIcon, noop } from './graphUtils';
import { useCarbonChartData } from './hooks/useCarbonChartData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import { RoundedCard } from './RoundedCard';
import CarbonChartTooltip from './tooltips/CarbonChartTooltip';

interface CarbonChartProps {
  datetimes: Date[];
  timeRange: TimeRange;
}

function CarbonChart({ datetimes, timeRange }: CarbonChartProps) {
  const { data, isLoading, isError } = useCarbonChartData();
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
    return (
      <NotEnoughDataMessage
        title="country-history.carbonintensity"
        id={Charts.CARBON_CHART}
      />
    );
  }
  return (
    <RoundedCard className="pb-2">
      <ChartTitle
        titleText={t(`country-history.carbonintensity.${timeRange}`)}
        badge={badge}
        unit={'gCO₂eq / kWh'}
        isEstimated={Boolean(text)}
        id={Charts.CARBON_CHART}
        className="mb-0.5"
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
      />
      <AreaGraph
        testId="details-carbon-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        height="8em"
        datetimes={datetimes}
        selectedTimeRange={timeRange}
        tooltip={CarbonChartTooltip}
      />
      <div className="pb-1 pt-2">
        <HorizontalColorbar colorScale={co2ColorScale} ticksCount={6} id={'co2'} />
      </div>
    </RoundedCard>
  );
}

export default CarbonChart;
