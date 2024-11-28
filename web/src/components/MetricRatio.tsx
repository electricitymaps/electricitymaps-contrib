import { FormatParameters } from 'utils/formatting';

interface MetricRatioProps {
  value: number;
  total?: number | null | undefined;
  format: (parameters: FormatParameters) => string | number;
  label?: string;
  useTotalUnit?: boolean;
}

// TODO(Cady): make separate component for just formatted value?
export function MetricRatio({
  value,
  total,
  format,
  label,
  useTotalUnit,
}: MetricRatioProps) {
  let formattedValue: string | number = '?';
  if (Number.isFinite(value)) {
    formattedValue = useTotalUnit ? format({ value, total }) : format({ value });
  }

  const formattedTotal = total && Number.isFinite(total) ? format({ value: total }) : '?';
  const labelAppendix = label ? ` ${label}` : '';

  if (!total) {
    return <small>{`${formattedValue} ${labelAppendix}`}</small>;
  }

  return <small>{`(${formattedValue} / ${formattedTotal}${labelAppendix})`}</small>;
}
