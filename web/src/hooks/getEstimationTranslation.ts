import { useTranslation } from 'react-i18next';

export function useGetEstimationTranslation(
  field: 'title' | 'pill' | 'body',
  estimationMethod?: string,
  estimatedPercentage?: number
) {
  const { t } = useTranslation();

  const exactTranslation =
    (estimatedPercentage ?? 0) > 0 && estimationMethod === 'aggregated'
      ? t(`estimation-card.aggregated_estimated.${field}`, {
          percentage: estimatedPercentage,
        })
      : t(`estimation-card.${estimationMethod?.toLowerCase()}.${field}`);

  const genericTranslation = t(`estimation-card.estimated_generic_method.${field}`);
  return exactTranslation.startsWith('estimation-card.')
    ? genericTranslation
    : exactTranslation;
}
