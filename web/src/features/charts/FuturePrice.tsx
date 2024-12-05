import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import { i18n, TFunction } from 'i18next';
import { useAtom } from 'jotai';
import { ChevronsDownUpIcon, ChevronsUpDownIcon, Clock3, Info } from 'lucide-react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { FuturePriceData } from 'types';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { getDateTimeFormatOptions } from 'utils/formatting';
import { futurePriceCollapsedAtom } from 'utils/state/atoms';

import {
  calculatePriceBound,
  dateIsFirstHourOfTomorrow,
  filterPriceData,
  getGranularity,
  negativeToPostivePercentage,
  normalizeToGranularity,
  priceIn5Percentile,
} from './futurePriceUtils';

export function FuturePrice({ futurePrice }: { futurePrice: FuturePriceData | null }) {
  const { t, i18n } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useAtom(futurePriceCollapsedAtom);
  const granularity = getGranularity(futurePrice?.priceData);
  const usedGranularity = 30;

  const filteredPriceData = filterPriceData(futurePrice?.priceData, usedGranularity);

  const maxPriceTotal = useMemo(
    () => calculatePriceBound(filteredPriceData, Math.max, granularity),
    [filteredPriceData, granularity]
  );
  const minPriceTotal = useMemo(
    () => calculatePriceBound(filteredPriceData, Math.min, granularity),
    [filteredPriceData, granularity]
  );
  const maxPriceFuture = useMemo(
    () => calculatePriceBound(filteredPriceData, Math.max, granularity, true),
    [filteredPriceData, granularity]
  );
  const minPriceFuture = useMemo(
    () => calculatePriceBound(filteredPriceData, Math.min, granularity, true),
    [filteredPriceData, granularity]
  );
  const hasNegativePrice = minPriceTotal < 0;
  const negativePercentage = negativeToPostivePercentage(minPriceTotal, maxPriceTotal);

  if (!futurePrice || !isFuturePrice(futurePrice)) {
    return null;
  }

  return (
    <div className="pt-2">
      <Accordion
        isCollapsed={isCollapsed}
        title={t(`country-panel.price-chart.see`)}
        expandedTitle={t(`country-panel.price-chart.hide`)}
        className="text-success dark:text-success-dark"
        expandedIcon={ChevronsUpDownIcon}
        collapsedIcon={ChevronsDownUpIcon}
        iconClassName="text-success dark:text-success-dark"
        iconSize={20}
        setState={setIsCollapsed}
        onOpen={() => trackEvent(TrackEvent.FUTURE_PRICE_EXPANDED)}
      >
        <div data-testid="future-price">
          <PriceDisclaimer />
          <TimeDisclaimer />
          {futurePrice?.priceData && (
            <ul>
              {Object.entries(filteredPriceData).map(
                ([date, price]: [string, number]) => (
                  <li
                    key={date}
                    className={
                      isNow(date, granularity)
                        ? `rounded-md bg-price-light/10 dark:bg-price-dark/10`
                        : ''
                    }
                  >
                    <div>
                      {dateIsFirstHourOfTomorrow(new Date(date)) && (
                        <div className="flex flex-col py-1" data-testid="tomorrow-label">
                          <HorizontalDivider />
                          <TommorowLabel date={date} t={t} i18n={i18n} />
                        </div>
                      )}
                      <div className="flex flex-row justify-items-end gap-2 px-1">
                        <TimeDisplay date={date} granularity={granularity} />
                        <PriceDisplay
                          price={price}
                          currency={futurePrice.currency}
                          i18n={i18n}
                        />
                        <div className="flex h-full w-full flex-row self-center">
                          {hasNegativePrice && price < 0 && (
                            <div
                              className="flex flex-row justify-end"
                              style={{
                                width: `calc(100% * ${
                                  negativePercentage / 100
                                } + 12px - 12px * ${negativePercentage / 100})`,
                              }}
                              data-testid="negative-price"
                            >
                              <PriceBar
                                price={price}
                                maxPrice={-1 * minPriceTotal}
                                color={getColor(
                                  price,
                                  maxPriceFuture,
                                  minPriceFuture,
                                  date,
                                  granularity
                                )}
                              />
                            </div>
                          )}
                          {price >= 0 && (
                            <div
                              data-testid="positive-price"
                              style={{
                                width: `calc(100% * ${
                                  (100 - negativePercentage) / 100
                                } + 12px - 12px * ${(100 - negativePercentage) / 100})`,
                              }}
                              className="ml-auto"
                            >
                              {price >= 0 && (
                                <PriceBar
                                  price={price}
                                  maxPrice={maxPriceTotal}
                                  color={getColor(
                                    price,
                                    maxPriceFuture,
                                    minPriceFuture,
                                    date,
                                    granularity
                                  )}
                                />
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                )
              )}
            </ul>
          )}
        </div>
      </Accordion>
    </div>
  );
}

function TommorowLabel({ date, t, i18n }: { date: string; t: TFunction; i18n: i18n }) {
  const formattedDate = Intl.DateTimeFormat(i18n.language, {
    dateStyle: 'medium',
  }).format(new Date(date));

  return (
    <p className="py-1 font-semibold">
      {`${t('country-panel.price-chart.tomorrow')}, ${formattedDate}`}
    </p>
  );
}

export function PriceBar({
  price,
  maxPrice,
  color,
}: {
  price: number;
  maxPrice: number;
  color: string;
}) {
  const nonNegativePrice = Math.abs(price);
  return (
    <div
      className={`h-3 rounded-full ${color}`}
      style={{
        width: `calc(calc(${nonNegativePrice / maxPrice} * (100% - 12px)) + 12px)`,
      }}
      data-testid="price-bar"
    />
  );
}

function PriceDisplay({
  price,
  currency,
  i18n,
}: {
  price: number;
  currency: string;
  i18n: i18n;
}) {
  const priceString = Intl.NumberFormat(i18n.languages[0], {
    style: 'currency',
    currency: currency,
    maximumSignificantDigits: 4,
    currencyDisplay: 'narrowSymbol',
  }).format(price);
  return (
    <p
      className={`min-w-[66px] overflow-clip text-nowrap text-sm font-semibold tabular-nums ${
        Number.isNaN(Number(priceString.at(-1))) ? 'text-end' : 'text-start'
      }`}
    >
      {priceString}
    </p>
  );
}

function TimeDisplay({ date, granularity }: { date: string; granularity: number }) {
  const { i18n } = useTranslation();
  const { t } = useTranslation();
  const datetime = new Date(date);

  if (isNow(date, granularity)) {
    return (
      <p className={`min-w-18 pl-1 text-sm font-semibold`} data-testid="now-label">
        {t(`country-panel.price-chart.now`)}
      </p>
    );
  }

  const formattedDate = Intl.DateTimeFormat(i18n.language, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(datetime);

  return <p className={`min-w-18 text-nowrap text-sm tabular-nums`}>{formattedDate}</p>;
}

function PriceDisclaimer() {
  const { t } = useTranslation();
  return (
    <Disclaimer
      testId="price-disclaimer"
      Icon={<Info size={16} />}
      text={t('country-panel.price-chart.price-disclaimer')}
      className="flex flex-row py-2 text-amber-700 dark:text-amber-500"
    />
  );
}

function TimeDisclaimer() {
  const { t } = useTranslation();
  const { i18n } = useTranslation();
  const date = Intl.DateTimeFormat(
    i18n.language,
    getDateTimeFormatOptions(TimeAverages.HOURLY)
  ).formatToParts(new Date());
  return (
    <Disclaimer
      Icon={<Clock3 size={16} />}
      text={`${t('country-panel.price-chart.time-disclaimer')} ${date.at(-1)?.value}.`}
      className="flex flex-row pb-3 text-neutral-600 dark:text-gray-300"
      testId="time-disclaimer"
    />
  );
}

function Disclaimer({
  className,
  testId,
  Icon,
  text,
}: {
  className?: string;
  testId?: string;
  Icon: React.ReactNode;
  text: string;
}) {
  return (
    <div className={className} data-testid={testId}>
      {Icon}
      <p className="pl-1 text-xs font-semibold">{text}</p>
    </div>
  );
}

const getColor = (
  price: number,
  maxPrice: number,
  minPrice: number,
  date: string,
  granularity: number
): string => {
  if (
    normalizeToGranularity(new Date(date), granularity) <
    normalizeToGranularity(new Date(), granularity)
  ) {
    return 'bg-price-light dark:bg-price-dark opacity-50';
  } else if (
    priceIn5Percentile(price, maxPrice, minPrice, true) &&
    maxPrice != minPrice
  ) {
    return 'bg-danger dark:bg-red-400';
  } else if (
    priceIn5Percentile(price, maxPrice, minPrice, false) &&
    maxPrice != minPrice
  ) {
    return 'bg-success dark:bg-success-dark';
  } else {
    return 'bg-price-light dark:bg-price-dark';
  }
};

const isNow = (date: string, granularity: number): boolean =>
  normalizeToGranularity(new Date(date), granularity).getTime() ===
  normalizeToGranularity(new Date(), granularity).getTime();

const isFuturePrice = (FuturePriceData: FuturePriceData): boolean => {
  const keys = Object.keys(FuturePriceData.priceData);
  const lastKey = keys.at(-1);
  if (!lastKey) {
    return false;
  }
  return new Date(lastKey) > new Date();
};
