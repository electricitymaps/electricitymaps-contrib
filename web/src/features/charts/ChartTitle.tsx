/* eslint-disable react/jsx-no-target-blank */
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { timeAverageAtom } from 'utils/state/atoms';

type Props = {
  translationKey: string;
  unit?: string;
  badge?: React.ReactElement;
};

export function ChartTitle({ translationKey, unit, badge }: Props) {
  const { t } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  /*
  Use local for timeAverage if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <div className="flex flex-col pb-0.5">
      <div className="flex items-center gap-1.5 pt-4">
        <h2 className="grow">{t(`${translationKey}.${timeAverage}`)}</h2>
        {badge}
      </div>
      {unit && <div className="text-sm dark:text-gray-300">{unit}</div>}
    </div>
  );
}
