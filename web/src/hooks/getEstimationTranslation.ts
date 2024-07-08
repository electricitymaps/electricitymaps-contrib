import { useTranslation } from 'react-i18next';
import { EstimationMethods } from 'utils/constants';

export function useGetEstimationTranslation(
  field: 'title' | 'pill' | 'body',
  estimationMethod?: EstimationMethods,
  estimatedPercentage?: number
) {
  const { t } = useTranslation();
  const exactTranslation = estimatedPercentage
    ? t(`estimation-card.aggregated_estimated.${field}`, {
        percentage: estimatedPercentage,
      })
    : t(`estimation-card.${estimationMethod}.${field}`);

  const genericTranslation = t(`estimation-card.estimated_generic_method.${field}`);
  return exactTranslation.startsWith('estimation-card.')
    ? genericTranslation
    : exactTranslation;
}
