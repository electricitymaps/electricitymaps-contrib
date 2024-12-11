import { useTranslation } from 'react-i18next';

import { useNetExchangeChartData } from './hooks/useNetExchangeChartData';

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

  const isWithinPrevious48Hours =
    date < new Date(chartData[0].datetime) || date < new Date(chartData.at(-1)!.datetime);

  // TODO(cady): consider using a heuristic - if >20% of exchanges are missing?
  const isMissingExchangeData = chartData.some(({ meta: { exchange } }) =>
    Object.values<number | null>(exchange).includes(null)
  );

  // Show disclaimer if exchanges cover previous 48 hours and exchange data has null (unreported) values
  if (isWithinPrevious48Hours && isMissingExchangeData) {
    return (
      <p className="prose my-1 rounded bg-gray-200 p-2 text-xs leading-snug dark:bg-gray-800 dark:text-white dark:prose-a:text-white">
        {t('country-history.exchange-delay')}
      </p>
    );
  }
}
