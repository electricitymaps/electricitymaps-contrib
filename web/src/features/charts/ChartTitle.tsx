/* eslint-disable react/jsx-no-target-blank */
import EstimationBadge from 'components/EstimationBadge';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { HiOutlineArrowDownTray } from 'react-icons/hi2';
import { timeAverageAtom } from 'utils/state/atoms';

type Props = {
  translationKey: string;
  hasLink?: boolean;
  badgeText?: string;
};

export function ChartTitle({
  translationKey,
  hasLink = true,
  badgeText = undefined,
}: Props) {
  const { t } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  /*
  Use local for timeAverage if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <>
      <div className="flex flex-row justify-between pb-0.5 pt-4">
        <h3 className="text-md font-bold">{t(`${translationKey}.${timeAverage}`)}</h3>
        {badgeText != undefined && <EstimationBadge text={badgeText} />}
      </div>
      {hasLink && (
        <div className="flex flex-row items-center pb-2 text-center text-[0.7rem]">
          <HiOutlineArrowDownTray className="min-w-[12px]" size={12} />
          <a
            href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=country_panel"
            target="_blank"
            rel="noreferrer"
            className="pl-0.5 text-left text-[#4178ac] no-underline hover:underline dark:invert"
          >
            {t('country-history.Getdata')}
          </a>
        </div>
      )}
    </>
  );
}
