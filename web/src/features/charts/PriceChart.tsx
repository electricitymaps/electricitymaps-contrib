import { useTranslation } from 'react-i18next';
import { Charts, TimeAverages } from 'utils/constants';

import { ChartTitle } from './ChartTitle';
import { DisabledMessage } from './DisabledMessage';
import AreaGraph from './elements/AreaGraph';
import { FuturePrice } from './FuturePrice';
import { noop } from './graphUtils';
import { usePriceChartData } from './hooks/usePriceChartData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
import { RoundedCard } from './RoundedCard';
import PriceChartTooltip from './tooltips/PriceChartTooltip';

interface PriceChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function PriceChart({ datetimes, timeAverage }: PriceChartProps) {
  const { data, isLoading, isError } = usePriceChartData();
  const { t } = useTranslation();

  if (isLoading || isError || !data) {
    return null;
  }
  let { chartData } = data;
  const {
    layerFill,
    layerKeys,
    layerStroke,
    valueAxisLabel,
    markerFill,
    priceDisabledReason,
    futurePrice,
  } = data;

  const isPriceDisabled = Boolean(priceDisabledReason);

  if (isPriceDisabled) {
    // Randomize price values to ensure the chart is not empty
    chartData = chartData.map((layer) => ({
      ...layer,
      layerData: { ...layer.layerData, price: Math.random() },
    }));
  }

  if (!Number.isFinite(chartData[0]?.layerData?.price)) {
    return null;
  }

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  if (!hasEnoughDataToDisplay) {
    return (
      <NotEnoughDataMessage
        id={Charts.PRICE_CHART}
        title="country-history.electricityprices"
      />
    );
  }

  return (
    <RoundedCard>
      <ChartTitle
        titleText={t(`country-history.electricityprices.${timeAverage}`)}
        unit={valueAxisLabel}
        id={Charts.PRICE_CHART}
      />
      <div className="relative">
        {isPriceDisabled && (
          <DisabledMessage
            message={t(`country-panel.disabledPriceReasons.${priceDisabledReason}`)}
          />
        )}
        <AreaGraph
          testId="history-prices-graph"
          data={chartData}
          layerKeys={layerKeys}
          layerStroke={layerStroke}
          layerFill={layerFill}
          markerFill={markerFill}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          height="6em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={PriceChartTooltip}
          isDisabled={isPriceDisabled}
        />
      </div>
      <FuturePrice futurePrice={futurePrice} />
    </RoundedCard>
  );
}

export default PriceChart;
