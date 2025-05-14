import { useColorScale } from 'hooks/theme';
import { CarbonUnits } from 'utils/units';

export function Square({ value }: { value: number }) {
  const colorScale = useColorScale();

  return (
    <div
      className="h-2 w-2"
      style={{
        backgroundColor: value > 0 ? colorScale(value) : '#D4D9DE',
      }}
    />
  );
}

export function RenewablePercentageDisplay({
  value,
  className,
  withSquare = false,
}: {
  value: number | undefined;
  className?: string;
  withSquare?: boolean;
}) {
  const valueAsNumber = value || 0;
  return (
    <>
      {withSquare && <Square value={valueAsNumber} />}
      <p className={className}>
        <b>{value == null ? '?' : Math.round(valueAsNumber)}</b>&nbsp;%
      </p>
    </>
  );
}

export function CarbonIntensityDisplay({
  co2Intensity,
  className,
  withSquare = false,
}: {
  co2Intensity: number | undefined;
  className?: string;
  withSquare?: boolean;
}) {
  const intensityAsNumber = co2Intensity || 0;
  return (
    <>
      {withSquare && <Square value={intensityAsNumber} />}
      <p className={className}>
        <b>{co2Intensity == null ? '?' : Math.round(intensityAsNumber)}</b>&nbsp;
        {CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR}
      </p>
    </>
  );
}
