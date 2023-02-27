import type { Maybe } from 'types';

interface MetricRatioProps {
  value: number;
  total: Maybe<number>;
  format: (value: number) => string | number;
}

export function MetricRatio({ value, total, format }: MetricRatioProps) {
  const formattedValue = Number.isFinite(value) && value ? format(value) : '?';
  const formattedTotal = Number.isFinite(total) && total ? format(total) : '?';

  return <small>{`(${formattedValue} / ${formattedTotal})`}</small>;
}
