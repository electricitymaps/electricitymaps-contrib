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
  priceData: { [key: string]: number } | undefined,
  granularity: number
): { [key: string]: number } => {
  if (!priceData) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(priceData).filter(
      ([dateString]) => new Date(dateString).getMinutes() % granularity === 0
    )
  );
};

export const getGranularity = (
  priceData: { [key: string]: number } | undefined
): number => {
  if (!priceData) {
    return 0;
  }
  const priceDataKeys = Object.keys(priceData);
  return priceDataKeys.length > 1
    ? (new Date(priceDataKeys[1]).getTime() - new Date(priceDataKeys[0]).getTime()) /
        60_000
    : 0;
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
    .map(([, price]: [string, number]) => price);

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

export const priceIn5Percentile = (
  price: number,
  maxPrice: number,
  minPrice: number,
  inTop: boolean
): boolean => {
  const fivePercent = 0.05;
  const priceRange = maxPrice - minPrice;

  if (inTop) {
    return price >= maxPrice - priceRange * fivePercent;
  }
  return price <= minPrice + priceRange * fivePercent;
};
