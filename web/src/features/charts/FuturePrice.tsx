import Accordion from 'components/Accordion';
import { useAtomValue } from 'jotai';
import { ChevronsDownUpIcon, ChevronsUpDownIcon, Info } from 'lucide-react';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { FuturePriceData } from 'types';
import { TimeAverages } from 'utils/constants';
import { formatDateTick } from 'utils/formatting';
import { futurePriceCollapsed } from 'utils/state/atoms';

import { convertPrice } from './bar-breakdown/utils';

export function FuturePrice({ futurePrice }: { futurePrice: FuturePriceData | null }) {
  const { t } = useTranslation();
  const isCollapsed = useAtomValue(futurePriceCollapsed);
  const granularity = getGranularity(futurePrice?.priceData ?? {});

  const maxPriceTotal = useMemo(
    () => calculatePrice(futurePrice, Math.max, granularity),
    [futurePrice, granularity]
  );
  const maxPriceFuture = useMemo(
    () => calculatePrice(futurePrice, Math.max, granularity, true),
    [futurePrice, granularity]
  );
  const minPriceFuture = useMemo(
    () => calculatePrice(futurePrice, Math.min, granularity, true),
    [futurePrice, granularity]
  );

  if (!futurePrice) {
    return null;
  }

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
        <>
          <PriceDisclaimer />
          {futurePrice?.priceData && (
            <ul>
              {Object.entries(futurePrice.priceData).map(
                ([date, price]: [string, number]) => (
                  <li key={date}>
                    <div className="flex flex-row justify-items-end gap-2">
                      <TimeDisplay date={date} granularity={granularity} />
                      <p className="min-w-[65px] text-nowrap text-sm font-semibold tabular-nums">
                        {`${getValueOfConvertPrice(price, futurePrice.currency)} ${t(
                          `country-panel.price-chart.${futurePrice.currency}`
                        )}`}
                      </p>
                      <div className="h-full w-full self-center">
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
                      </div>
                    </div>
                  </li>
                )
              )}
            </ul>
          )}
        </>
      </Accordion>
    </div>
  );
}

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
  futurePrice: FuturePriceData | null,
  callback: (...values: number[]) => number,
  granularity: number,
  isFuture: boolean = false
) => {
  if (!futurePrice) {
    return 0;
  }

  const prices = Object.entries(futurePrice.priceData)
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
    return <p className="min-w-[84px] text-sm"> {t(`country-panel.price-chart.now`)}</p>;
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
    <div className="flex flex-row py-3 text-neutral-600 dark:text-gray-300">
      <Info size={16} />
      <p className="pl-1 text-xs font-semibold">
        {t('country-panel.price-chart.disclaimer')}
      </p>
    </div>
  );
}
