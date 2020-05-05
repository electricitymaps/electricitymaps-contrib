import { isFinite } from 'lodash';

export function getRatioPercent(value, total) {
  const perc = Math.round(value / total * 10000) / 100;
  return isFinite(perc) ? `${perc}` : '?';
}

export function tonsPerHourToGramsPerMinute(value) {
  return value / 1e6 / 60.0;
}

export function calculateLengthFromDimensions(x, y) {
  return isFinite(x) && isFinite(y) ? Math.sqrt(x * x + y * y) : null;
}
