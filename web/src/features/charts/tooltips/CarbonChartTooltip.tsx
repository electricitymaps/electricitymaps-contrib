/* eslint-disable unicorn/no-null */
import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { MapColorSource } from 'utils/constants';
import { getZoneValueForColor, round } from 'utils/helpers';
import { isConsumptionAtom, timeRangeAtom } from 'utils/state/atoms';

import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function CarbonChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const timeRange = useAtomValue(timeRangeAtom);
  const { t } = useTranslation();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const co2ColorScale = useCo2ColorScale();

  if (!zoneDetail) {
    return null;
  }
  const {
    co2intensity,
    co2intensityProduction,
    stateDatetime,
    estimationMethod,
    estimatedPercentage,
  } = zoneDetail;
  const intensity = getZoneValueForColor(
    { c: { ci: co2intensity }, p: { ci: co2intensityProduction }, pr: null },
    isConsumption,
    MapColorSource.CARBON_INTENSITY
  );
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationPill =
    Boolean(estimationMethod) || Boolean(roundedEstimatedPercentage);
  return (
    <div
      data-testid="carbon-chart-tooltip"
      className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-neutral-700 dark:bg-neutral-800 sm:w-[410px]"
    >
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeRange={timeRange}
        squareColor={co2ColorScale(intensity)}
        title={t('tooltips.carbonintensity')}
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={roundedEstimatedPercentage}
        estimationMethod={estimationMethod}
      />
      <CarbonIntensityDisplay
        co2Intensity={intensity}
        className="flex justify-center text-base"
      />
    </div>
  );
}
