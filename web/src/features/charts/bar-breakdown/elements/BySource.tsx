import EstimationBadge from 'components/EstimationBadge';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { TFunction } from 'i18next';
import { useAtom } from 'jotai';
import { CircleDashed, TrendingUpDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { EstimationMethods, TimeAverages } from 'utils/constants';
import {
  displayByEmissionsAtom,
  productionConsumptionAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

const getText = (
  timePeriod: TimeAverages,
  dataType: 'emissions' | 'production' | 'consumption',
  t: TFunction
) => {
  const translations = {
    hourly: {
      emissions: t('country-panel.by-source.emissions'),
      production: t('country-panel.by-source.electricity-production'),
      consumption: t('country-panel.by-source.electricity-consumption'),
    },
    default: {
      emissions: t('country-panel.by-source.total-emissions'),
      production: t('country-panel.by-source.total-electricity-production'),
      consumption: t('country-panel.by-source.total-electricity-consumption'),
    },
  };
  const period = timePeriod === TimeAverages.HOURLY ? 'hourly' : 'default';
  return translations[period][dataType];
};

export default function BySource({
  className,
  hasEstimationPill = false,
  estimatedPercentage,
  unit,
  estimationMethod,
}: {
  className?: string;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  unit?: string | number;
  estimationMethod?: EstimationMethods;
}) {
  const { t } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);

  const dataType = displayByEmissions ? 'emissions' : mixMode;
  const text = getText(timeAverage, dataType, t);
  const pillText = useGetEstimationTranslation(
    'pill',
    estimationMethod,
    estimatedPercentage
  );

  return (
    <div className="flex flex-col pb-1 pt-4">
      <div
        className={`text-md relative flex flex-row justify-between font-bold ${className}`}
      >
        <div className="flex gap-1">
          <h2>{text}</h2>
        </div>
        {hasEstimationPill && (
          <EstimationBadge
            text={pillText}
            Icon={
              estimationMethod === EstimationMethods.TSA ? CircleDashed : TrendingUpDown
            }
          />
        )}
      </div>
      {unit && <p className="dark:text-gray-300">{unit}</p>}
    </div>
  );
}
