/* eslint-disable unicorn/no-null */
import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { getCarbonIntensity, round } from 'utils/helpers';
import { isConsumptionAtom, isHourlyAtom, timeRangeAtom } from 'utils/state/atoms';

import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function CarbonChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const timeRange = useAtomValue(timeRangeAtom);
  const { t } = useTranslation();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const co2ColorScale = useCo2ColorScale();
  const isHourly = useAtomValue(isHourlyAtom);

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
  const intensity = getCarbonIntensity(
    { c: { ci: co2intensity }, p: { ci: co2intensityProduction } },
    isConsumption
  );
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationOrAggregationPill = Boolean(estimationMethod) || !isHourly;
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
        hasEstimationOrAggregationPill={hasEstimationOrAggregationPill}
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
