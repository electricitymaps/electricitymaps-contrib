interface MetricRatioProps {
  value: number;
  total: number;
  format: (value: number, total?: number) => string | number;
  label?: string;
  useTotalUnit?: boolean;
}

export function MetricRatio({
  value,
  total,
  format,
  label,
  useTotalUnit,
}: MetricRatioProps) {
  let formattedValue: string | number = '?';
  if (Number.isFinite(value)) {
    formattedValue = useTotalUnit ? format(value, total) : format(value);
  }

  const formattedTotal = Number.isFinite(total) ? format(total) : '?';
  const labelAppendix = label ? ` ${label}` : '';

  return <small>{`(${formattedValue} / ${formattedTotal}${labelAppendix})`}</small>;
}
