/* eslint-disable react/jsx-no-target-blank */
import { useScrollAnchorIntoView } from 'hooks/useScrollAnchorIntoView';
import { useAtomValue } from 'jotai';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { timeAverageAtom } from 'utils/state/atoms';

type Props = {
  translationKey: string;
  unit?: string;
  badge?: React.ReactElement;
  id?: string;
};

export function ChartTitle({ translationKey, unit, badge, id }: Props) {
  const { t } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const reference = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (id && reference.current) {
      reference.current.id = id;
    }
  }, [reference, id]);

  useScrollAnchorIntoView(reference);
  /*
  Use local for timeAverage if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <div className="flex flex-col pb-0.5">
      <div className="flex items-center gap-1.5 pt-4">
        <h2 className="grow" id={id} key={id} ref={reference}>
          {t(`${translationKey}.${timeAverage}`)}
        </h2>
        {badge}
      </div>
      {unit && <div className="text-sm dark:text-gray-300">{unit}</div>}
    </div>
  );
}
