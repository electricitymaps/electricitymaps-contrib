/* eslint-disable react/jsx-no-target-blank */
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { timeAverageAtom } from 'utils/state/atoms';

type Props = {
  translationKey: string;
  unit?: string;
  id?: string;
  badge?: React.ReactElement;
};

export function ChartTitle({ translationKey, unit, id, badge }: Props) {
  const { t } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const title = t(`${translationKey}.${timeAverage}`);

  /*
  Use local for timeAverage if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <div className="flex flex-col pb-0.5">
      <div className="flex items-center gap-1.5 pt-4">
        <a href={`#${id}`}>
          <h2 className="grow" id={id}>
            {title}
          </h2>
        </a>
        {badge}
      </div>
      {unit && <div className="text-sm dark:text-gray-300">{unit}</div>}
    </div>
  );
}
