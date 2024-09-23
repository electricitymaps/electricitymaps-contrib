import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import { i18n, TFunction } from 'i18next';
import { useAtomValue } from 'jotai';
import { ChevronsDownUpIcon, ChevronsUpDownIcon, Clock3, Info } from 'lucide-react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { FuturePriceData } from 'types';
import { TimeAverages } from 'utils/constants';
import { formatDateTick, getDateTimeFormatOptions } from 'utils/formatting';
import { futurePriceCollapsed } from 'utils/state/atoms';

import { convertPrice } from './bar-breakdown/utils';

export function FuturePrice({ futurePrice }: { futurePrice: FuturePriceData | null }) {
  const { t, i18n } = useTranslation();
  const isCollapsed = useAtomValue(futurePriceCollapsed);
  const granularity = getGranularity(futurePrice?.priceData ?? {});
  const usedGranularity = 30;

  const filteredPriceData = filterPriceData(
    futurePrice?.priceData ?? {},
    usedGranularity
  );

  const maxPriceTotal = useMemo(
    () => calculatePrice(filteredPriceData, Math.max, granularity),
    [filteredPriceData, granularity]
  );
  const minPriceTotal = useMemo(
    () => calculatePrice(filteredPriceData, Math.min, granularity),
    [filteredPriceData, granularity]
  );
  const maxPriceFuture = useMemo(
    () => calculatePrice(filteredPriceData, Math.max, granularity, true),
    [filteredPriceData, granularity]
  );
  const minPriceFuture = useMemo(
    () => calculatePrice(filteredPriceData, Math.min, granularity, true),
    [filteredPriceData, granularity]
  );

  if (!futurePrice) {
    return null;
  }

  const hasNegativePrice = minPriceTotal < 0;
  const negativePercentage = negativeToPostivePercentage(minPriceTotal, maxPriceTotal);

  return (
    <div className="pt-2">
      <Accordion
        isCollapsedDefault={isCollapsed}
        title={t(`country-panel.price-chart.see`)}
        expandedTitle={t(`country-panel.price-chart.hide`)}
        className="text-success dark:text-emerald-500"
        expandedIcon={ChevronsUpDownIcon}
        collapsedIcon={ChevronsDownUpIcon}
        iconClassName="text-success dark:text-emerald-500"
        iconSize={20}
        isCollapsedAtom={futurePriceCollapsed}
      >
        <div data-test-id="future-price">
          <PriceDisclaimer />
          <TimeDisclaimer />
          {futurePrice?.priceData && (
            <ul>
              {Object.entries(filteredPriceData).map(
                ([date, price]: [string, number]) => (
                  <li key={date}>
                    {dateIsFirstHourOfTomorrow(new Date(date)) && (
                      <div className="flex flex-col py-1" data-test-id="tomorrow-label">
                        <HorizontalDivider />
                        <TommorowLabel date={date} t={t} i18n={i18n} />
                      </div>
                    )}
                    <div className="flex flex-row justify-items-end gap-2">
                      <TimeDisplay date={date} granularity={granularity} />
                      <p className="min-w-[64px] text-nowrap text-sm font-semibold tabular-nums">
                        {`${getValueOfConvertPrice(price, futurePrice.currency)} ${t(
                          `country-panel.price-chart.${futurePrice.currency}`
                        )}`}
                      </p>
                      <div className="flex h-full w-full flex-row self-center ">
                        {hasNegativePrice && (
                          <div
                            className="flex flex-row justify-end "
                            style={{
                              width: `${hasNegativePrice ? negativePercentage : 0}%`,
                            }}
                            data-test-id="negative-price"
                          >
                            {price < 0 && (
                              <PriceBars
                                price={price * -1}
                                maxPrice={-1 * minPriceTotal}
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
                        <div
                          style={{
                            width: `${
                              hasNegativePrice ? 100 - negativePercentage : 100
                            }%`,
                          }}
                          data-test-id="positive-price"
                        >
                          {price > 0 && (
                            <PriceBars
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

function negativeToPostivePercentage(minPrice: number, maxPrice: number): number {
  return Math.round(Math.abs((minPrice / (maxPrice + Math.abs(minPrice))) * 100));
}

function TommorowLabel({ date, t, i18n }: { date: string; t: TFunction; i18n: i18n }) {
  const formattedDate = Intl.DateTimeFormat(i18n.language, {
    month: 'short',
    year: 'numeric',
    day: 'numeric',
  }).formatToParts(new Date(date));
  console.log(formattedDate);
  return (
    <p className="py-1 font-semibold">
      {`${t('country-panel.price-chart.tomorrow')}, ${formattedDate[0].value} ${
        formattedDate[2].value
      } ${formattedDate[4].value}`}
    </p>
  );
}

const dateIsFirstHourOfTomorrow = (date: Date): boolean =>
  date.getHours() === 0 && date.getMinutes() == 0 && date.getDay() != new Date().getDay();

const filterPriceData = (
  priceData: { [key: string]: number },
  granularity: number
): { [key: string]: number } =>
  Object.fromEntries(
    Object.entries(priceData).filter(([dateString]) => {
      const date = new Date(dateString);
      return date.getMinutes() % granularity === 0;
    })
  );

const getGranularity = (priceData: { [key: string]: number | undefined }): number => {
  const priceDataKeys = Object.keys(priceData);
  return priceDataKeys.length > 1
    ? (new Date(priceDataKeys[1]).getTime() - new Date(priceDataKeys[0]).getTime()) /
        60_000
    : 0;
};

const getValueOfConvertPrice = (price: number, currency: string): number | undefined => {
  const { value } = convertPrice(price, currency);
  return value;
};

const calculatePrice = (
  priceData: { [key: string]: number },
  callback: (...values: number[]) => number,
  granularity: number,
  isFuture: boolean = false
) => {
  if (!priceData) {
    return 0;
  }

  const prices = Object.entries(priceData)
    .filter(([dateString]) => {
      if (!isFuture) {
        return true;
      }
      const date = new Date(dateString);
      return (
        normalizeToGranularity(date, granularity) >=
        normalizeToGranularity(new Date(), granularity)
      );
    })
    .map(([_, price]: [string, number]) => price);

  return callback(...prices);
};

export function PriceBars({
  price,
  maxPrice,
  color,
}: {
  price: number;
  maxPrice: number;
  color: string;
}) {
  return (
    <div
      className={`h-3 rounded-full ${color}`}
      style={{ width: `${(price / maxPrice) * 100}%` }}
      data-test-id="price-bar"
    ></div>
  );
}

const getColor = (
  price: number,
  maxPrice: number,
  minPrice: number,
  date: string,
  granularity: number
): string => {
  if (price === maxPrice) {
    return 'bg-danger dark:bg-red-400';
  } else if (price === minPrice) {
    return 'bg-success dark:bg-emerald-500';
  } else if (
    normalizeToGranularity(new Date(date), granularity) <
    normalizeToGranularity(new Date(), granularity)
  ) {
    return 'bg-[#18214F] dark:bg-[#848EC0] opacity-50';
  } else {
    return 'bg-[#18214F] dark:bg-[#848EC0]';
  }
};

const normalizeToGranularity = (date: Date, granularity: number) => {
  const normalizedDate = new Date(date);
  const minutes = normalizedDate.getMinutes();
  const normalizedMinutes = Math.floor(minutes / granularity) * granularity;
  normalizedDate.setMinutes(normalizedMinutes, 0, 0);
  return normalizedDate;
};

function TimeDisplay({ date, granularity }: { date: string; granularity: number }) {
  const { i18n } = useTranslation();
  const { t } = useTranslation();
  const datetime = new Date(date);

  if (
    normalizeToGranularity(datetime, granularity).getTime() ==
    normalizeToGranularity(new Date(), granularity).getTime()
  ) {
    return (
      <p className="min-w-[84px] text-sm" data-test-id="now-label">
        {' '}
        {t(`country-panel.price-chart.now`)}
      </p>
    );
  }

  const formatdate = formatDateTick(datetime, i18n.language, TimeAverages.HOURLY);

  return (
    <p className="min-w-[84px] text-nowrap text-sm tabular-nums">
      {`${t(`country-panel.price-chart.at`)}  ${formatdate}`}
    </p>
  );
}

function PriceDisclaimer() {
  const { t } = useTranslation();
  return (
    <div
      className="flex flex-row py-2 text-amber-700 dark:text-amber-500"
      data-test-id="price-disclaimer"
    >
      <Info size={16} />
      <p className="pl-1 text-xs font-semibold">
        {t('country-panel.price-chart.price-disclaimer')}
      </p>
    </div>
  );
}

function TimeDisclaimer() {
  const { t } = useTranslation();
  const { i18n } = useTranslation();
  return (
    <div
      className="flex flex-row pb-3 text-neutral-600 dark:text-gray-300"
      data-test-id="time-disclaimer"
    >
      <Clock3 size={16} />
      <p className="pl-1 text-xs font-semibold">
        {`${t('country-panel.price-chart.time-disclaimer')} ${
          Intl.DateTimeFormat(
            i18n.language,
            getDateTimeFormatOptions(TimeAverages.HOURLY)
          ).formatToParts(new Date())[12].value
        }.`}
      </p>
    </div>
  );
}
