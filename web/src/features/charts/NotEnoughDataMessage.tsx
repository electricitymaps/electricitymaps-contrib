import { useTranslation } from 'translation/translation';

import { ChartTitle } from './ChartTitle';

export function NotEnoughDataMessage({ title }: { title: string }) {
  const { __ } = useTranslation();
  return (
    <div className="w-full">
      <ChartTitle translationKey={title} hasLink={false} />
      <div className="my-2 rounded bg-gray-200 py-4 text-center text-sm dark:bg-gray-800">
        <p>{__('country-history.not-enough-data')}</p>
      </div>
    </div>
  );
}
