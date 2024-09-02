import Accordion from 'components/Accordion';
import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import { ChevronsDownUpIcon, ChevronsUpDownIcon, Info } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FuturePriceData, Price } from 'types';
import { Day, TimeAverages } from 'utils/constants';
import { formatDateTick } from 'utils/formatting';
import { dayAheadPriceDayAtom } from 'utils/state/atoms';

import { ChartTitle } from './ChartTitle';
import { DisabledMessage } from './DisabledMessage';
import AreaGraph from './elements/AreaGraph';
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

  const futurePriceData: FuturePriceData = {
    entryCount: 24,
    futurePrices: {
      '2024-09-01 22:00:00+00:00': { price: 0.03 },
      '2024-09-01 23:00:00+00:00': { price: 0.02 },
      '2024-09-02 00:00:00+00:00': { price: 0.01 },
      '2024-09-02 01:00:00+00:00': { price: 0.01 },
      '2024-09-02 02:00:00+00:00': { price: 0.01 },
      '2024-09-02 03:00:00+00:00': { price: 0.01 },
      '2024-09-02 04:00:00+00:00': { price: 0.01 },
      '2024-09-02 05:00:00+00:00': { price: 0.01 },
      '2024-09-02 06:00:00+00:00': { price: 0.01 },
      '2024-09-02 07:00:00+00:00': { price: 0.01 },
      '2024-09-02 08:00:00+00:00': { price: 0.01 },
      '2024-09-02 09:00:00+00:00': { price: 0.01 },
      '2024-09-02 10:00:00+00:00': { price: 0.01 },
      '2024-09-02 11:00:00+00:00': { price: 0.01 },
      '2024-09-02 12:00:00+00:00': { price: 0.01 },
      '2024-09-02 13:00:00+00:00': { price: 0.04 },
      '2024-09-02 14:00:00+00:00': { price: 0.01 },
      '2024-09-02 15:00:00+00:00': { price: 0.01 },
      '2024-09-02 16:00:00+00:00': { price: 0.01 },
      '2024-09-02 17:00:00+00:00': { price: 0.01 },
      '2024-09-02 18:00:00+00:00': { price: 0.01 },
      '2024-09-02 19:00:00+00:00': { price: 0.01 },
      '2024-09-02 20:00:00+00:00': { price: 0.01 },
      '2024-09-02 21:00:00+00:00': { price: 0.05 },
      '2024-09-02 22:00:00+00:00': { price: 0.11 },
      '2024-09-02 23:00:00+00:00': { price: 0.09 },
      '2024-09-03 00:00:00+00:00': { price: 0.05 },
      '2024-09-04 01:00:00+00:00': { price: 0.04 },
    },
    currency: 'EUR',
    source: 'nordpool.com',
    zoneKey: 'FR',
  };

  return (
    <RoundedCard>
      <ChartTitle
        translationKey="country-history.electricityprices"
        unit={valueAxisLabel}
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
          isMobile={false}
          height="6em"
          datetimes={datetimes}
          selectedTimeAggregate={timeAverage}
          tooltip={PriceChartTooltip}
          isDisabled={isPriceDisabled}
        />
      </div>
      <FuturePrice priceData={futurePriceData} />
    </RoundedCard>
  );
}

function FuturePrice({ priceData }: { priceData: FuturePriceData | null }) {
  const { t } = useTranslation();
  const [currentDay, setCurrentDay] = useAtom(dayAheadPriceDayAtom);
  if (!priceData) {
    return null;
  }
  const maxPrice = Math.max(
    ...Object.entries(priceData.futurePrices)
      .slice(currentDay == Day.Today ? 0 : 24, currentDay == Day.Today ? 24 : 48)
      .map(([_, price]: [string, Price]) => price.price)
  );

  const minPrice = Math.min(
    ...Object.entries(priceData.futurePrices).map(
      ([_, price]: [string, Price]) => price.price
    )
  );

  console.log('maxPrice', maxPrice);

  const toggleOptions = [
    { value: Day.Today, translationKey: 'country-panel.price-chart.today' },
    { value: Day.Tomorrow, translationKey: 'country-panel.price-chart.tomorrow' },
  ];

  const onSetCurrentDay = (option: string) => {
    if (option === currentDay) {
      return;
    }
    setCurrentDay(currentDay === Day.Today ? Day.Tomorrow : Day.Today);
  };
  return (
    <div className="pt-2">
      <Accordion
        title={t(`country-panel.price-chart.see`)}
        expandedTitle={t(`country-panel.price-chart.hide`)}
        className="text-success dark:text-emerald-500"
        expandedIcon={ChevronsUpDownIcon}
        collapsedIcon={ChevronsDownUpIcon}
        iconClassName="text-success dark:text-emerald-500"
        iconSize={20}
      >
        <>
          <ToggleButton
            options={toggleOptions}
            selectedOption={currentDay}
            onToggle={onSetCurrentDay}
          />
          <PriceDisclaimer />
          {priceData?.futurePrices && (
            <ul>
              {Object.entries(priceData.futurePrices)
                .slice(
                  currentDay == Day.Today ? 0 : 24,
                  currentDay == Day.Today ? 24 : 48
                )
                .map(([date, price]: [string, Price]) => (
                  <li key={date}>
                    <div className="flex flex-row justify-items-end gap-1">
                      <TimeDisplay date={date} />
                      <p className="min-w-16 text-sm font-semibold">
                        {price.price.toFixed(2)}{' '}
                        {t(`country-panel.price-chart.${priceData.currency}`)}
                      </p>
                      <div className="h-full w-full self-center">
                        <PriceBars
                          price={price.price}
                          maxPrice={maxPrice}
                          minPrice={minPrice}
                        />
                      </div>
                    </div>
                  </li>
                ))}
            </ul>
          )}
        </>
      </Accordion>
    </div>
  );
}

export function PriceBars({
  price,
  maxPrice,
  minPrice,
}: {
  price: number;
  maxPrice: number;
  minPrice: number;
}) {
  const color = getColor(price, maxPrice, minPrice);
  return (
    <div
      className={`h-3 rounded-full ${color}`}
      style={{ width: `${(price / maxPrice) * 100}%` }}
    ></div>
  );
}

const getColor = (price: number, maxPrice: number, minPrice: number): string => {
  if (price === maxPrice) {
    return 'bg-danger dark:bg-red-400';
  } else if (price === minPrice) {
    return 'bg-success dark:bg-emerald-500';
  } else {
    return 'bg-[#18214F] dark:bg-[#848EC0]';
  }
};

function TimeDisplay({ date }: { date: string }) {
  const { i18n } = useTranslation();
  const { t } = useTranslation();
  const datetime = new Date(date);

  console.log('datetime', datetime);
  console.log('new Date()', new Date());

  if (
    datetime.getFullYear() === new Date().getFullYear() &&
    datetime.getMonth() === new Date().getMonth() &&
    datetime.getDate() === new Date().getDate() &&
    datetime.getHours() === new Date().getHours()
  ) {
    return <p className="min-w-[85px] text-sm"> {t(`country-panel.price-chart.now`)}</p>;
  }

  const formatdate = formatDateTick(datetime, i18n.language, TimeAverages.HOURLY);

  return (
    <p className="min-w-[85px] text-sm">{`${t(
      `country-panel.price-chart.at`
    )} ${formatdate}`}</p>
  );
}

function PriceDisclaimer() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-row py-3 text-neutral-600 dark:text-gray-300">
      <Info size={16} />
      <p className="pl-1 text-xs font-semibold">
        {t('country-panel.price-chart.disclaimer')}
      </p>
    </div>
  );
}

export default PriceChart;
