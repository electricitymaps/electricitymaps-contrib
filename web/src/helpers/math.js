import { isFinite } from 'lodash';

export function getRatioPercent(value, total) {
  const perc = Math.round(value / total * 10000) / 100;
  return isFinite(perc) ? `${perc}` : '?';
}
