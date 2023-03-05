interface MetricRatioProps {
  value: number;
  total: number;
  format: (value: number) => string | number;
}

export function MetricRatio({ value, total, format }: MetricRatioProps) {
  const formattedValue = Number.isFinite(value) ? format(value) : '?';
  const formattedTotal = Number.isFinite(total) ? format(total) : '?';

  return <small>{`(${formattedValue} / ${formattedTotal})`}</small>;
}
