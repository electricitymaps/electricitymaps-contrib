import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import ZoneHeaderTitle from './ZoneHeaderTitle';

interface ZoneHeaderProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
  co2intensity?: number;
  renewableRatio?: number;
  fossilFuelRatio?: number;
}

export function ZoneHeader({
  zoneId,
  isEstimated,
  isAggregated,
  co2intensity,
  renewableRatio,
  fossilFuelRatio,
}: ZoneHeaderProps) {
  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      <ZoneHeaderTitle
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
      />
      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare co2intensity={co2intensity ?? Number.NaN} withSubtext />
        <CircularGauge
          name="Low-carbon"
          ratio={fossilFuelRatio ? 1 - fossilFuelRatio : Number.NaN}
        />
        <CircularGauge name="Renewable" ratio={renewableRatio ?? Number.NaN} />
      </div>
    </div>
  );
}
