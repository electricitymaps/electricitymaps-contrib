import { isFinite } from 'lodash';

export function getRatioPercent(value, total) {
  // If both the numerator and denominator are zeros,
  // interpret the ratio as zero instead of NaN.
  if (value === 0 && total === 0) {
    return 0;
  }
  if (!isFinite(value) || !isFinite(total)) {
    return '?';
  }
  return Math.round(value / total * 10000) / 100;
}

export function tonsPerHourToGramsPerMinute(value) {
  return value / 1e6 / 60.0;
}

export function calculateLengthFromDimensions(x, y) {
  return isFinite(x) && isFinite(y) ? Math.sqrt(x * x + y * y) : null;
}
