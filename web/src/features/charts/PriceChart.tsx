import { useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import { ChartTitle } from './ChartTitle';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';
import { usePriceChartData } from './hooks/usePriceChartData';
import PriceChartTooltip from './tooltips/PriceChartTooltip';

interface PriceChartProps {
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function PriceChart({ datetimes, timeAverage }: PriceChartProps) {
  const { data, isLoading, isError } = usePriceChartData();
  const { __ } = useTranslation();

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
  return (
    <>
      <ChartTitle translationKey="country-history.electricityprices" />
      <div className="relative">
        {isPriceDisabled && (
          <div className="absolute top-0 h-full w-full">
            <div className=" h-full w-full rounded bg-white opacity-50 dark:bg-gray-700" />
            <div className="absolute top-[50%] left-[50%] z-10 w-60 -translate-x-1/2 -translate-y-1/2 rounded-sm bg-gray-200 p-2 text-center text-sm shadow-lg dark:bg-gray-900">
              {__(`country-panel.disabledPriceReasons.${priceDisabledReason}`)}
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
