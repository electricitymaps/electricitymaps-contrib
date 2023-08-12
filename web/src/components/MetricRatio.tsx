import { useTranslation } from 'translation/translation';
import { formatCo2, formatPower, formatPowerWithSameUnit } from 'utils/formatting';

interface MetricRatioProps {
  value: number;
  total: number;
  type: 'power' | 'co2';
}

export function MetricRatio({ value, total, type }: MetricRatioProps) {
  const { __ } = useTranslation();
  let formattedTotal = null;
  let formattedValue = null;
  if (type === 'power') {
    formattedValue = Number.isFinite(value) ? formatPowerWithSameUnit(value, total) : '?';
    formattedTotal = Number.isFinite(total) ? formatPower(total) : '?';
  }

  if (type === 'co2') {
    formattedValue = Number.isFinite(value) ? `${formatCo2(value, total)}` : '?';
    formattedTotal = Number.isFinite(total)
      ? `${formatCo2(total)} ${__('ofCO2eqPerHour')}`
      : '?';
  }
  return <small>{`(${formattedValue} / ${formattedTotal})`}</small>;
}
