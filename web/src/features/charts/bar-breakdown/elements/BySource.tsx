import EstimationBadge from 'components/EstimationBadge';
import { TFunction } from 'i18next';
import { PlugCircleBoltIcon } from 'icons/plugCircleBoltIcon';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { TimeAverages } from 'utils/constants';
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

function getEstimatedText(
  t: TFunction,
  estimatedPercentage?: number,
  estimationMethod?: string
) {
  if (estimatedPercentage) {
    return t('estimation-card.aggregated_estimated.pill', {
      percentage: estimatedPercentage,
    });
  }
  if (estimationMethod === 'threshold_filtered') {
    return t('estimation-card.threshold_filtered.pill');
  }

  return t('estimation-badge.fully-estimated');
}

export default function BySource({
  className,
  hasEstimationPill = false,
  estimatedPercentage,
  estimationMethod,
}: {
  className?: string;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  estimationMethod?: string;
}) {
  const { t } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);

  const dataType = displayByEmissions ? 'emissions' : mixMode;
  const text = getText(timeAverage, dataType, t);

  return (
    <div
      className={`relative flex flex-row justify-between pb-2 pt-4 text-md font-bold ${className}`}
    >
      <div className="flex gap-1">
        <PlugCircleBoltIcon />
        {text}
      </div>
      {hasEstimationPill && (
        <EstimationBadge
          text={getEstimatedText(t, estimatedPercentage, estimationMethod)}
        />
      )}
    </div>
  );
}
