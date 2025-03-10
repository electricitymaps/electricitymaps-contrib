import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatCo2 } from 'utils/formatting';
import { round } from 'utils/helpers';
import { isConsumptionAtom, timeRangeAtom } from 'utils/state/atoms';

import { getTotalEmissionsAvailable } from '../graphUtils';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function EmissionChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const timeRange = useAtomValue(timeRangeAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);
  const { t } = useTranslation();

  if (!zoneDetail) {
    return null;
  }

  const totalEmissions = getTotalEmissionsAvailable(zoneDetail, isConsumption);
  const { stateDatetime, estimationMethod, estimatedPercentage } = zoneDetail;
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationPill =
    Boolean(estimationMethod) || Boolean(roundedEstimatedPercentage);

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:border dark:border-gray-700 dark:bg-gray-800 sm:w-[410px]">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeRange={timeRange}
        squareColor="#a5292a"
        title={t('country-panel.emissions')}
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={roundedEstimatedPercentage}
        estimationMethod={estimationMethod}
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{formatCo2({ value: totalEmissions })}</b> {t('ofCO2eq')}
      </p>
    </div>
  );
}
