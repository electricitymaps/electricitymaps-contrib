import HorizontalColorbar from 'components/legend/ColorBar';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { Charts, TimeRange } from 'utils/constants';
import { round } from 'utils/helpers';
import { isHourlyAtom } from 'utils/state/atoms';

import { ChartSubtitle, ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { EstimationLegend } from './elements/EstimationMarkers';
import { noop } from './graphUtils';
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
  const isHourly = useAtomValue(isHourlyAtom);

  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData, layerFill, layerKeys } = data;

  const hasEnoughDataToDisplay = datetimes?.length > 2;
  const valueAxisLabel = 'gCO₂eq / kWh';

  const estimated = chartData.map((d) => {
    const zoneDetail = d.meta;
    const { estimationMethod, estimatedPercentage } = zoneDetail;
    const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
    const hasEstimationPill =
      estimationMethod != undefined || Boolean(roundedEstimatedPercentage);

    return hasEstimationPill;
  });
  const estimationMethod = chartData.find((d) => d.meta.estimationMethod)?.meta
    .estimationMethod;
  const someEstimated = estimated.some(Boolean);

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
        isEstimated={someEstimated}
        unit={someEstimated ? undefined : valueAxisLabel}
        id={Charts.CARBON_CHART}
        className="mb-0.5"
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
      />
      {someEstimated && (
        <EstimationLegend
          isAggregated={!isHourly}
          estimationMethod={estimationMethod}
          valueAxisLabel={valueAxisLabel}
        />
      )}
      <AreaGraph
        testId="details-carbon-graph"
        data={chartData}
        layerKeys={layerKeys}
        layerFill={layerFill}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        height="8em"
        datetimes={datetimes}
        estimated={estimated}
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
