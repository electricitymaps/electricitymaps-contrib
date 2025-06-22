import { useTranslation } from 'react-i18next';
import { Charts } from 'utils/constants';

import { ChartTitle } from './ChartTitle';

export function NotEnoughDataMessage({ title, id }: { title: string; id: Charts }) {
  const { t } = useTranslation();
  return (
    <div className="w-full">
      <ChartTitle titleText={title} id={id} />
      <div className="my-2 rounded bg-neutral-200 py-4 text-center text-sm dark:bg-neutral-800">
        <p>{t(($) => $['country-history']['not-enough-data'])}</p>
      </div>
    </div>
  );
}
