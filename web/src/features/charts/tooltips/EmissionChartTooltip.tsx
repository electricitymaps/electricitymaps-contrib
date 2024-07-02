import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatCo2 } from 'utils/formatting';
import { productionConsumptionAtom, timeAverageAtom } from 'utils/state/atoms';

import { getTotalEmissionsAvailable } from '../graphUtils';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

export default function EmissionChartTooltip({ zoneDetail }: InnerAreaGraphTooltipProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);
  const { t } = useTranslation();

  if (!zoneDetail) {
    return null;
  }

  const totalEmissions = getTotalEmissionsAvailable(zoneDetail, mixMode);
  const { stateDatetime, estimationMethod, estimatedPercentage } = zoneDetail;
  const hasEstimationPill = Boolean(estimationMethod) || Boolean(estimatedPercentage);

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl sm:w-[410px] dark:border dark:border-gray-700 dark:bg-gray-800">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#a5292a"
        title={t('country-panel.emissions')}
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={estimatedPercentage}
        estimationMethod={estimationMethod}
      />
      <p className="flex justify-center text-base">
        <b className="mr-1">{formatCo2(totalEmissions)}</b> {t('ofCO2eq')}
      </p>
    </div>
  );
}
