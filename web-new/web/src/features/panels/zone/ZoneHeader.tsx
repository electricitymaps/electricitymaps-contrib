import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import ZoneHeaderTitle from './ZoneHeaderTitle';
import { productionConsumptionAtom } from 'utils/state/atoms';
import { Mode } from 'utils/constants';
import { useAtom } from 'jotai';

interface ZoneHeaderProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
  co2intensity?: number;
  renewableRatio?: number;
  fossilFuelRatio?: number;
  co2intensityProduction?: number;
  renewableRatioProduction?: number;
  fossilFuelRatioProduction?: number;
}

export function ZoneHeader({
  zoneId,
  isEstimated,
  isAggregated,
  co2intensity,
  renewableRatio,
  fossilFuelRatio,
  co2intensityProduction,
  renewableRatioProduction,
  fossilFuelRatioProduction,
}: ZoneHeaderProps) {
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const intensity = isConsumption ? co2intensity : co2intensityProduction;
  const renewable = isConsumption ? renewableRatio : renewableRatioProduction;
  const fossilFuel = isConsumption ? fossilFuelRatio : fossilFuelRatioProduction;

  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      <ZoneHeaderTitle
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
      />
      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare co2intensity={intensity ?? Number.NaN} withSubtext />
        <CircularGauge
          name="Low-carbon"
          ratio={fossilFuel ? 1 - fossilFuel : Number.NaN}
        />
        <CircularGauge name="Renewable" ratio={renewable ?? Number.NaN} />
      </div>
    </div>
  );
}
