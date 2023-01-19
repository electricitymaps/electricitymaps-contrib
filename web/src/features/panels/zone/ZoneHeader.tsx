import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';
import ZoneHeaderTitle from './ZoneHeaderTitle';

function LowCarbonTooltip() {
  const { __ } = useTranslation();
  return (
    <div className="text-left">
      <b>{__('tooltips.lowcarbon')}</b>
      <br />
      <small>{__('tooltips.lowCarbDescription')}</small>
      <br />
    </div>
  );
}

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
  const { __ } = useTranslation();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const intensity = isConsumption ? co2intensity : co2intensityProduction;
  const renewable = isConsumption ? renewableRatio : renewableRatioProduction;
  const fossilFuel = (isConsumption ? fossilFuelRatio : fossilFuelRatioProduction) ?? 0;

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
          name={__('country-panel.lowcarbon')}
          ratio={1 - fossilFuel}
          tooltipContent={<LowCarbonTooltip />}
        />
        <CircularGauge
          name={__('country-panel.renewable')}
          ratio={renewable ?? Number.NaN}
        />
      </div>
    </div>
  );
}
