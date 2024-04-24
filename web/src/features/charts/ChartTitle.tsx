/* eslint-disable react/jsx-no-target-blank */
import EstimationBadge from 'components/EstimationBadge';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { timeAverageAtom } from 'utils/state/atoms';

type Props = {
  translationKey: string;
  hasLink?: boolean;
  badgeText?: string;
  icon?: JSX.Element;
};

export function ChartTitle({ translationKey, badgeText = undefined, icon }: Props) {
  const { t } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  /*
  Use local for timeAverage if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <div className="flex flex-row justify-between pb-0.5 pt-4">
      <div className="flex content-center gap-1.5">
        {icon && <div className="w-5">{icon}</div>}
        <h3 className="text-md font-bold">{t(`${translationKey}.${timeAverage}`)}</h3>
      </div>
      {badgeText != undefined && <EstimationBadge text={badgeText} />}
    </div>
  );
}
