import { TFunction } from 'i18next';
import { EstimationMethods } from 'utils/constants';
import { round } from 'utils/helpers';

export default function getEstimationOrAggregationTranslation(
  t: TFunction,
  field: 'title' | 'pill' | 'body' | 'legend',
  isAggregated: boolean,
  estimationMethod?: EstimationMethods,
  estimatedPercentage: number = 0
) {
  // TODO: This method mixes too many concerns and too many cases. Refactor required.

  if (field === 'legend') {
    const correctedEstimationMethod =
      estimationMethod ?? EstimationMethods.GENERAL_PURPOSE_ZONE_MODEL;

    const isPreliminary =
      correctedEstimationMethod == EstimationMethods.FORECASTS_HIERARCHY ||
      correctedEstimationMethod == EstimationMethods.TSA;
    const isSynthetic = !isPreliminary;
    if (isSynthetic) {
      return t('estimation-card.synthetic');
    }
    if (isPreliminary) {
      return t('estimation-card.preliminary');
    }
  }

  if (isAggregated) {
    // Aggregated data will show a label that doesn't depend on the estimation method.
    if (estimatedPercentage > 1) {
      const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
      return t(`estimation-card.aggregated_estimated.${field}`, {
        percentage: roundedEstimatedPercentage,
      });
    } else {
      // Just aggregated, no estimation
      return t(`estimation-card.aggregated.${field}`);
    }
  } else {
    // This is not aggregated data

    if (field === 'pill') {
      const isPreliminary =
        estimationMethod == EstimationMethods.FORECASTS_HIERARCHY ||
        estimationMethod == EstimationMethods.TSA;
      // TODO: outage is not an estimation, need to refactor out to keep separation of concerns.
      const isOutage = estimationMethod == EstimationMethods.OUTAGE;
      const isSynthetic = !isPreliminary;
      if (isSynthetic) {
        return t('estimation-card.synthetic');
      }
      if (isPreliminary) {
        return t('estimation-card.preliminary');
      }
      if (isOutage) {
        return t(`estimation-card.outage.pill`);
      }
    } else {
      // TODO: in order to have a clear separation of concerns, the decision of the label
      // to show shouldn't be made in the translation file, and thus, the translation file should be
      // independent of the estimation method.
      return t(`estimation-card.${estimationMethod}.${field}`);
    }
  }
}
