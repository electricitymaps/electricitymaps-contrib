import Badge from 'components/Badge';
import { useAtom } from 'jotai';
import { TranslationFunction, useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import {
  displayByEmissionsAtom,
  productionConsumptionAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

const getText = (
  timePeriod: TimeAverages,
  dataType: 'emissions' | 'production' | 'consumption',
  __: TranslationFunction
) => {
  const translations = {
    hourly: {
      emissions: __('country-panel.by-source.emissions'),
      production: __('country-panel.by-source.electricity-production'),
      consumption: __('country-panel.by-source.electricity-consumption'),
    },
    default: {
      emissions: __('country-panel.by-source.total-emissions'),
      production: __('country-panel.by-source.total-electricity-production'),
      consumption: __('country-panel.by-source.total-electricity-consumption'),
    },
  };
  const period = timePeriod === TimeAverages.HOURLY ? 'hourly' : 'default';
  return translations[period][dataType];
};

export default function BySource({
  className,
  hasEstimationPill = false,
}: {
  className?: string;
  hasEstimationPill?: boolean;
}) {
  const { __ } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);

  const dataType = displayByEmissions ? 'emissions' : mixMode;
  const text = getText(timeAverage, dataType, __);

  return (
    <div
      className={`relative flex flex-row justify-between pb-2 pt-4 text-md font-bold ${className}`}
    >
      {text}
      {hasEstimationPill && (
        <Badge
          pillText={__('estimation-badge.fully-estimated')}
          type="warning"
          icon="h-[16px] w-[16px] bg-[url('/images/estimated_light.svg')] bg-center dark:bg-[url('/images/estimated_dark.svg')]"
        />
      )}
    </div>
  );
}
