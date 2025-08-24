import { useCo2ColorScale } from 'hooks/theme';
import { CarbonUnits } from 'utils/units';

function Square({ co2Intensity }: { co2Intensity: number }) {
  const co2ColorScale = useCo2ColorScale();

  return (
    <div
      className="h-2 w-2"
      style={{
        backgroundColor: co2Intensity > 0 ? co2ColorScale(co2Intensity) : '#D4D9DE',
      }}
    />
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
      {withSquare && <Square co2Intensity={intensityAsNumber} />}
      <p className={className}>
        <b>{co2Intensity == null ? '?' : Math.round(intensityAsNumber)}</b>&nbsp;
        {CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR}
      </p>
    </>
  );
}
