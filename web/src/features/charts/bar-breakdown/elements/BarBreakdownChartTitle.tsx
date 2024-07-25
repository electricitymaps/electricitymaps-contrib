import { ChartTitle } from 'features/charts/ChartTitle';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { useAtomValue } from 'jotai';
import { EstimationMethods } from 'utils/constants';
import {
  displayByEmissionsAtom,
  isHourlyAtom,
  productionConsumptionAtom,
} from 'utils/state/atoms';

const getTranslationKey = (
  isHourly: boolean,
  dataType: 'emissions' | 'production' | 'consumption'
) => {
  const translations = {
    hourly: {
      emissions: 'emissions',
      production: 'electricity-production',
      consumption: 'electricity-consumption',
    },
    default: {
      emissions: 'total-emissions',
      production: 'total-electricity-production',
      consumption: 'total-electricity-consumption',
    },
  };
  const period = isHourly ? 'hourly' : 'default';
  return 'country-panel.by-source.' + translations[period][dataType];
};

export default function BarBreakdownChartTitle({
  estimatedPercentage,
  unit,
  estimationMethod,
}: {
  estimatedPercentage?: number;
  unit?: string;
  estimationMethod?: EstimationMethods;
}) {
  const isHourly = useAtomValue(isHourlyAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const mixMode = useAtomValue(productionConsumptionAtom);

  const dataType = displayByEmissions ? 'emissions' : mixMode;
  const translationKey = getTranslationKey(isHourly, dataType);
  const pillText = useGetEstimationTranslation(
    'pill',
    estimationMethod,
    estimatedPercentage
  );

  return (
    <ChartTitle
      translationKey={translationKey}
      badgeText={pillText}
      unit={unit}
      hasTimeAverageTranslations={false}
    />
  );
}
