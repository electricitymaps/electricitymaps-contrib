/* eslint-disable unicorn/no-null */
import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { Mode } from 'utils/constants';
import { getCarbonIntensity } from 'utils/helpers';
import { productionConsumptionAtom, timeAverageAtom } from 'utils/state/atoms';

import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function CarbonChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { t } = useTranslation();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
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
  const intensity = getCarbonIntensity(
    { c: { ci: co2intensity }, p: { ci: co2intensityProduction } },
    isConsumption
  );
  const hasEstimationPill = Boolean(estimationMethod) || Boolean(estimatedPercentage);
  return (
    <div
      data-test-id="carbon-chart-tooltip"
      className="w-full rounded-md bg-white p-3 shadow-xl sm:w-[410px] dark:border dark:border-gray-700 dark:bg-gray-800"
    >
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor={co2ColorScale(intensity)}
        title={t('tooltips.carbonintensity')}
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={estimatedPercentage}
        estimationMethod={estimationMethod}
      />
      <CarbonIntensityDisplay
        co2Intensity={intensity}
        className="flex justify-center text-base"
      />
    </div>
  );
}
