import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { ZoneDetails } from 'types';
import { Mode } from 'utils/constants';
import { getCarbonIntensity, getFossilFuelRatio, getRenewableRatio } from 'utils/helpers';
import { productionConsumptionAtom, selectedDatetimeIndexAtom } from 'utils/state/atoms';

function LowCarbonTooltip() {
  const { t } = useTranslation();
  return (
    <div className="text-left">
      <b>{t('tooltips.lowcarbon')}</b>
      <br />
      <small>{t('tooltips.lowCarbDescription')}</small>
      <br />
    </div>
  );
}

export function ZoneHeaderGauges({ data }: { data?: ZoneDetails }) {
  const { t } = useTranslation();
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

  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare
          data-test-id="co2-square-value"
          intensity={intensity}
          withSubtext
        />
        <CircularGauge
          name={t('country-panel.lowcarbon')}
          ratio={fossilFuelPercentage}
          tooltipContent={<LowCarbonTooltip />}
          testId="zone-header-lowcarbon-gauge"
        />
        <CircularGauge
          name={t('country-panel.renewable')}
          ratio={renewable}
          testId="zone-header-renewable-gauge"
        />
      </div>
    </div>
  );
}
