interface MetricRatioProps {
  value: number;
  total: number;
  format: (value: number) => string | number;
  label?: string;
}

export function MetricRatio({ value, total, format, label }: MetricRatioProps) {
  const formattedValue = Number.isFinite(value) ? format(value) : '?';
  const formattedTotal = Number.isFinite(total) ? format(total) : '?';
  const labelAppendix = label ? ` ${label}` : '';

  return <small>{`(${formattedValue} / ${formattedTotal}${labelAppendix})`}</small>;
}
