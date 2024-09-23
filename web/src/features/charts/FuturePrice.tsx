import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import { i18n, TFunction } from 'i18next';
import { useAtom } from 'jotai';
import { ChevronsDownUpIcon, ChevronsUpDownIcon, Clock3, Info } from 'lucide-react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { FuturePriceData } from 'types';
import { TimeAverages } from 'utils/constants';
import { formatDateTick, getDateTimeFormatOptions } from 'utils/formatting';
import { futurePriceCollapsed } from 'utils/state/atoms';

import {
  calculatePriceBound,
  dateIsFirstHourOfTomorrow,
  filterPriceData,
  getGranularity,
  getValueOfConvertPrice,
  negativeToPostivePercentage,
  normalizeToGranularity,
} from './futurePriceUtils';

export function FuturePrice({ futurePrice }: { futurePrice: FuturePriceData | null }) {
  const { t, i18n } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useAtom(futurePriceCollapsed);
  const granularity = getGranularity(futurePrice?.priceData ?? {});
  const usedGranularity = 30;

  const filteredPriceData = filterPriceData(
    futurePrice?.priceData ?? {},
    usedGranularity
  );

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

  if (!futurePrice) {
    return null;
  }

  const hasNegativePrice = minPriceTotal < 0;
  const negativePercentage = negativeToPostivePercentage(minPriceTotal, maxPriceTotal);

  return (
    <div className="pt-2">
      <Accordion
        isCollapsed={isCollapsed}
        title={t(`country-panel.price-chart.see`)}
        expandedTitle={t(`country-panel.price-chart.hide`)}
        className="text-success dark:text-emerald-500"
        expandedIcon={ChevronsUpDownIcon}
        collapsedIcon={ChevronsDownUpIcon}
        iconClassName="text-success dark:text-emerald-500"
        iconSize={20}
        setState={setIsCollapsed}
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
                      <PriceDisplay price={price} currency={futurePrice.currency} t={t} />
                      <div className="flex h-full w-full flex-row self-center">
                        {hasNegativePrice && (
                          <div
                            className="flex flex-row justify-end"
                            style={{
                              width: `${negativePercentage}%`,
                            }}
                            data-test-id="negative-price"
                          >
                            {price < 0 && (
                              <PriceBar
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
                            width: `${100 - negativePercentage}%`,
                          }}
                          data-test-id="positive-price"
                        >
                          {price > 0 && (
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
    month: 'short',
    year: 'numeric',
    day: 'numeric',
  }).formatToParts(new Date(date));
  return (
    <p className="py-1 font-semibold">
      {`${t('country-panel.price-chart.tomorrow')}, ${formattedDate[0].value} ${
        formattedDate[2].value
      } ${formattedDate[4].value}`}
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
  return (
    <div
      className={`h-3 rounded-full ${color}`}
      style={{ width: `${(price / maxPrice) * 100}%` }}
      data-test-id="price-bar"
    />
  );
}

function PriceDisplay({
  price,
  currency,
  t,
}: {
  price: number;
  currency: string;
  t: TFunction;
}) {
  return (
    <p className="min-w-[64px] text-nowrap text-sm font-semibold tabular-nums">
      {`${getValueOfConvertPrice(price, currency)} ${t(
        `country-panel.price-chart.${currency}`
      )}`}
    </p>
  );
}

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
        {t(`country-panel.price-chart.now`)}
      </p>
    );
  }

  const formatdate = formatDateTick(datetime, i18n.language, TimeAverages.HOURLY);

  return (
    <p className="min-w-[84px] text-nowrap text-sm tabular-nums">
      {`${t(`country-panel.price-chart.at`)} ${formatdate}`}
    </p>
  );
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
  return (
    <Disclaimer
      Icon={<Clock3 size={16} />}
      text={`${t('country-panel.price-chart.time-disclaimer')} ${
        Intl.DateTimeFormat(
          i18n.language,
          getDateTimeFormatOptions(TimeAverages.HOURLY)
        ).formatToParts(new Date())[12].value
      }.`}
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
    <div className={className} data-test-id={testId}>
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
