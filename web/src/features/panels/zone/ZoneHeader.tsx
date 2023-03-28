import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { getFossilFuelPercentage } from 'utils/helpers';
import { productionConsumptionAtom, selectedDatetimeIndexAtom } from 'utils/state/atoms';
import ZoneHeaderTitle from './ZoneHeaderTitle';
import { ZoneDetails } from 'types';

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
  data: ZoneDetails | undefined;
  isAggregated?: boolean;
}

export function ZoneHeader({ zoneId, data, isAggregated }: ZoneHeaderProps) {
  const { __ } = useTranslation();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const selectedData = data?.zoneStates[selectedDatetime.datetimeString];

  const {
    co2intensity,
    renewableRatio,
    fossilFuelRatio,
    co2intensityProduction,
    renewableRatioProduction,
    fossilFuelRatioProduction,
    estimationMethod,
  } = selectedData || {};

  const intensity = isConsumption ? co2intensity : co2intensityProduction;
  const renewable = isConsumption ? renewableRatio : renewableRatioProduction;
  const fossilFuelPercentage = getFossilFuelPercentage(
    isConsumption,
    fossilFuelRatio,
    fossilFuelRatioProduction
  );
  const isEstimated = estimationMethod !== undefined;

  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      <ZoneHeaderTitle
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
      />
      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare
          data-test-id="co2-square-value"
          intensity={intensity ?? Number.NaN}
          withSubtext
        />
        <CircularGauge
          name={__('country-panel.lowcarbon')}
          ratio={fossilFuelPercentage}
          tooltipContent={<LowCarbonTooltip />}
          testId="zone-header-lowcarbon-gauge"
        />
        <CircularGauge
          name={__('country-panel.renewable')}
          ratio={renewable ?? Number.NaN}
          testId="zone-header-renewable-gauge"
        />
      </div>
    </div>
  );
}
