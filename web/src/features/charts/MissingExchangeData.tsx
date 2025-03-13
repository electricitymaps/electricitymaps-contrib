import { useTranslation } from 'react-i18next';

import { Y_AXIS_PADDING, Y_AXIS_WIDTH } from './elements/AreaGraph';
import { useNetExchangeChartData } from './hooks/useNetExchangeChartData';
import { AreaGraphElement } from './types';

const MARGIN = Y_AXIS_WIDTH - Y_AXIS_PADDING;
const SIGNIFICANT_THRESHOLD = 0.2;

const getTotal = (object: object) => Object.keys(object).length;
const getNulls = (object: object) =>
  Object.values(object).filter((v) => v === null).length;

function getIsMissingSignificantExchangeData(chartData: AreaGraphElement[]) {
  let nullCount = 0;
  let total = 0;
  for (const exchange of chartData.map(({ meta: { exchange } }) => exchange)) {
    nullCount += getNulls(exchange);
    total += getTotal(exchange);
  }
  return nullCount / total >= SIGNIFICANT_THRESHOLD;
}

export function MissingExchangeDataDisclaimer() {
  const { data, isLoading, isError } = useNetExchangeChartData();
  const { t } = useTranslation();

  if (isLoading || isError || !data) {
    return null;
  }

  const { chartData } = data;

  const date = new Date();
  date.setDate(date.getDate() - 1);
  date.setHours(0, 0, 0, 0);

  const isWithinPrevious48Hours = date < new Date(chartData.at(-1)!.datetime);
  const isMissingSignificantExchangeData = getIsMissingSignificantExchangeData(chartData);

  if (isWithinPrevious48Hours && isMissingSignificantExchangeData) {
    return (
      <p
        className="prose my-1 rounded bg-neutral-200 p-2 text-xs leading-snug dark:bg-neutral-800 dark:text-white dark:prose-a:text-white"
        style={{ width: `calc(100% - ${MARGIN}px)` }}
      >
        {t('country-history.exchange-delay')}
      </p>
    );
  }
  return null;
}
