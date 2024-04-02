import { useTranslation } from 'react-i18next';
import { TimeAverages } from 'utils/constants';

import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { usePriceChartData } from './hooks/usePriceChartData';
import { NotEnoughDataMessage } from './NotEnoughDataMessage';
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
  } = data;

  const isPriceDisabled = Boolean(priceDisabledReason);

  if (isPriceDisabled) {
    // Randomize price values to ensure the chart is not empty
    chartData = chartData.map((layer) => ({
      ...layer,
      layerData: { ...layer.layerData, price: Math.random() },
    }));
  }

  if (!chartData[0]?.layerData?.price) {
    return null;
  }

  const hasEnoughDataToDisplay = datetimes?.length > 2;

  if (!hasEnoughDataToDisplay) {
    return <NotEnoughDataMessage title="country-history.electricityprices" />;
  }

  return (
    <>
      <ChartTitle translationKey="country-history.electricityprices" />
      <div className="relative overflow-hidden">
        {isPriceDisabled && (
          <div className="absolute top-0 -ml-3 h-full w-[115%]">
            <div className="h-full w-full rounded bg-white opacity-90 dark:bg-gray-900" />
            <div className="absolute left-[45%] top-[50%] z-10 w-60 -translate-x-1/2 -translate-y-1/2 rounded-sm bg-gray-200 p-2 text-center text-sm shadow-lg dark:border dark:border-gray-700 dark:bg-gray-800">
              {t(`country-panel.disabledPriceReasons.${priceDisabledReason}`)}
            </div>
          </div>
        )}
        <AreaGraph
          testId="history-prices-graph"
          data={chartData}
          layerKeys={layerKeys}
          layerStroke={layerStroke}
          layerFill={layerFill}
          markerFill={markerFill}
          valueAxisLabel={valueAxisLabel}
          markerUpdateHandler={noop}
          markerHideHandler={noop}
          isMobile={false}
          height="6em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={PriceChartTooltip}
        />
      </div>
    </>
  );
}

export default PriceChart;
