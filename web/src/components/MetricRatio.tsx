export function MetricRatio({ value, total, format }) {
  const formattedValue = Number.isFinite(value) ? format(value) : '?';
  const formattedTotal = Number.isFinite(total) ? format(total) : '?';

  return <small>{`(${formattedValue} / ${formattedTotal})`}</small>;
}
