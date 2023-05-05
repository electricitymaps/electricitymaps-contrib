import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { getCarbonIntensity, getFossilFuelRatio, getRenewableRatio } from 'utils/helpers';
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

  const intensity = getCarbonIntensity(
    isConsumption,
    co2intensity,
    co2intensityProduction
  );
  const renewable = getRenewableRatio(
    isConsumption,
    renewableRatio,
    renewableRatioProduction
  );
  const fossilFuelPercentage = getFossilFuelRatio(
    isConsumption,
    fossilFuelRatio,
    fossilFuelRatioProduction
  );
  const isEstimated = estimationMethod !== undefined;

  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4" style={{ overflowY: 'auto' }}>
      <ZoneHeaderTitle
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
      />
      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare
          data-test-id="co2-square-value"
          intensity={intensity}
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
          ratio={renewable}
          testId="zone-header-renewable-gauge"
        />
      </div>
    </div>
  );
}
