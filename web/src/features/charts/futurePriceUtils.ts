import { convertPrice } from './bar-breakdown/utils';

export const normalizeToGranularity = (date: Date, granularity: number) => {
  const normalizedDate = new Date(date);
  const minutes = normalizedDate.getMinutes();
  const normalizedMinutes = Math.floor(minutes / granularity) * granularity;
  normalizedDate.setMinutes(normalizedMinutes, 0, 0);
  return normalizedDate;
};

export const dateIsFirstHourOfTomorrow = (date: Date): boolean =>
  date.getHours() === 0 && date.getMinutes() == 0 && date.getDay() != new Date().getDay();

export const filterPriceData = (
  priceData: { [key: string]: number },
  granularity: number
): { [key: string]: number } =>
  Object.fromEntries(
    Object.entries(priceData).filter(([dateString]) => {
      const date = new Date(dateString);
      return date.getMinutes() % granularity === 0;
    })
  );

export const getGranularity = (priceData: {
  [key: string]: number | undefined;
}): number => {
  const priceDataKeys = Object.keys(priceData);
  return priceDataKeys.length > 1
    ? (new Date(priceDataKeys[1]).getTime() - new Date(priceDataKeys[0]).getTime()) /
        60_000
    : 0;
};

export const getValueOfConvertPrice = (
  price: number,
  currency: string
): number | undefined => {
  const { value } = convertPrice(price, currency);
  return value;
};

export const calculatePriceBound = (
  priceData: { [key: string]: number },
  boundFunction: (...values: number[]) => number,
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

  return boundFunction(...prices);
};

export const negativeToPostivePercentage = (
  minPrice: number,
  maxPrice: number
): number => {
  if (minPrice >= 0) {
    return 0;
  }

  return Math.round(Math.abs((minPrice / (maxPrice + Math.abs(minPrice))) * 100));
};
export const getColor = (
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
