import { useTranslation } from 'react-i18next';
import { EstimationMethods } from 'utils/constants';
import { round } from 'utils/helpers';

export function useGetEstimationTranslation(
  field: 'title' | 'pill' | 'body',
  estimationMethod?: EstimationMethods,
  estimatedPercentage?: number
) {
  const { t } = useTranslation();
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const exactTranslation = roundedEstimatedPercentage
    ? t(`estimation-card.aggregated_estimated.${field}`, {
        percentage: roundedEstimatedPercentage,
      })
    : t(`estimation-card.${estimationMethod}.${field}`);

  const genericTranslation = t(`estimation-card.estimated_generic_method.${field}`);
  return exactTranslation.startsWith('estimation-card.')
    ? genericTranslation
    : exactTranslation;
}
