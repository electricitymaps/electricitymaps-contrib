import { useAtomValue } from 'jotai';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { StateZoneData } from 'types';
import { getCarbonIntensity, getFossilFuelRatio, getRenewableRatio } from 'utils/helpers';
import { isConsumptionAtom } from 'utils/state/atoms';

import CarbonIntensitySquare from './CarbonIntensitySquare';
import CircularGauge from './CircularGauge';

interface ZoneGaugesWithCO2SquareProps {
  zoneData: StateZoneData;
  withTooltips?: boolean;
  classNames?: string;
}

function ZoneGaugesWithCO2Square({
  zoneData,
  withTooltips = false,
  classNames,
}: ZoneGaugesWithCO2SquareProps) {
  const { t } = useTranslation();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const intensity = getCarbonIntensity(zoneData, isConsumption);
  const renewable = getRenewableRatio(zoneData, isConsumption);
  const fossilFuelPercentage = getFossilFuelRatio(zoneData, isConsumption);
  return (
    <div className={`flex w-full flex-row ${classNames}`}>
      <CarbonIntensitySquare
        data-testid="co2-square-value"
        intensity={intensity}
        tooltipContent={
          withTooltips ? <p>{t('tooltips.zoneHeader.carbonIntensity')}</p> : undefined
        }
      />
      <CircularGauge
        name={t('country-panel.lowcarbon')}
        ratio={fossilFuelPercentage}
        tooltipContent={
          withTooltips ? <p>{t('tooltips.zoneHeader.lowcarbon')}</p> : undefined
        }
        testId="zone-header-lowcarbon-gauge"
      />
      <CircularGauge
        name={t('country-panel.renewable')}
        ratio={renewable}
        tooltipContent={
          withTooltips ? <p>{t('tooltips.zoneHeader.renewable')}</p> : undefined
        }
        testId="zone-header-renewable-gauge"
      />
    </div>
  );
}

export default memo(ZoneGaugesWithCO2Square);
