import {
  calculatePriceBound,
  dateIsFirstHourOfTomorrow,
  filterPriceData,
  getGranularity,
  negativeToPostivePercentage,
  normalizeToGranularity,
  priceIn5Percentile,
} from './futurePriceUtils';

describe('FuturePrice Utility Functions', () => {
  test('normalizeToGranularity should round down to 30 minutes', () => {
    const date = new Date('2024-09-02T03:35:00Z');
    const granularity = 30;
    const normalizedDate = normalizeToGranularity(date, granularity);
    expect(normalizedDate.getMinutes()).to.equal(30);
    expect(normalizedDate.getSeconds()).to.equal(0);
  });

  test('normalizeToGranularity should round down to hours', () => {
    const date = new Date('2024-09-02T03:35:00Z');
    const granularity = 60;
    const normalizedDate = normalizeToGranularity(date, granularity);
    expect(normalizedDate.getMinutes()).to.equal(0);
    expect(normalizedDate.getSeconds()).to.equal(0);
  });

  test('dateIsFirstHourOfTomorrow returns true only is the first hour of the next day', () => {
    const tomorrow = new Date();
    tomorrow.setHours(0, 0, 0, 0);
    tomorrow.setDate(tomorrow.getDate() + 1);
    expect(dateIsFirstHourOfTomorrow(tomorrow)).to.equal(true);

    const tomorrowPlusHalfAnHour = new Date();
    tomorrowPlusHalfAnHour.setHours(0, 30, 0, 0);
    tomorrowPlusHalfAnHour.setDate(tomorrow.getDate() + 1);
    expect(dateIsFirstHourOfTomorrow(tomorrowPlusHalfAnHour)).to.equal(false);
  });

  test('filterPriceData filters out the dates that doesnt match the granularity', () => {
    const priceData = {
      '2024-09-02T03:00:00Z': 10,
      '2024-09-02T03:30:00Z': 20,
      '2024-09-02T04:00:00Z': 30,
    };
    const granularity = 60;
    const filteredData = filterPriceData(priceData, granularity);
    expect(Object.keys(filteredData).length).to.equal(2);
  });

  test('getGranularity returns time granularity of the data', () => {
    const priceData = {
      '2024-09-02T03:00:00Z': 10,
      '2024-09-02T03:30:00Z': 20,
      '2024-09-02T04:00:00Z': 30,
    };
    const granularity = getGranularity(priceData);
    expect(granularity).to.equal(30);
  });

  test('calculatePriceBound returns highest and lowest price in dataset', () => {
    const priceData = {
      '2024-09-02T03:00:00Z': -10,
      '2024-09-02T03:30:00Z': 30,
      '2024-09-02T04:00:00Z': 20,
    };

    const granularity = 15;
    const minPrice = calculatePriceBound(priceData, Math.min, granularity);
    expect(minPrice).to.equal(-10);

    const maxPrice = calculatePriceBound(priceData, Math.max, granularity);
    expect(maxPrice).to.equal(30);
  });

  test('negativeToPostivePercentage returns the correct percentage of negative to postive ratio', () => {
    const minPrice = -10;
    const maxPrice = 20;
    const percentage = negativeToPostivePercentage(minPrice, maxPrice);
    expect(percentage).to.equal(33);
  });

  test('negativeToPostivePercentage returns 0 if the min is above 0', () => {
    const minPrice = 10;
    const maxPrice = 20;
    const percentage = negativeToPostivePercentage(minPrice, maxPrice);
    expect(percentage).to.equal(0);
  });

  test('priceIn5Percentile returns true if price is in top 5 percentile', () => {
    const price = 95;
    const maxPrice = 100;
    const minPrice = 0;
    const inTop = true;
    const result = priceIn5Percentile(price, maxPrice, minPrice, inTop);
    expect(result).to.equal(true);
  });

  test('priceIn5Percentile returns false if price is not in top 5 percentile', () => {
    const price = 80;
    const maxPrice = 100;
    const minPrice = 50;
    const inTop = true;
    const result = priceIn5Percentile(price, maxPrice, minPrice, inTop);
    expect(result).to.equal(false);
  });

  test('priceIn5Percentile returns true if price is in bottom 5 percentile', () => {
    const price = 52;
    const maxPrice = 100;
    const minPrice = 50;
    const inTop = false;
    const result = priceIn5Percentile(price, maxPrice, minPrice, inTop);
    expect(result).to.equal(true);
  });

  test('priceIn5Percentile returns false if price is not in bottom 5 percentile', () => {
    const price = 60;
    const maxPrice = 100;
    const minPrice = 50;
    const inTop = false;
    const result = priceIn5Percentile(price, maxPrice, minPrice, inTop);
    expect(result).to.equal(false);
  });
});
