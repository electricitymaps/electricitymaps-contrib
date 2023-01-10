import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { formatTimeRange } from 'utils/formatting';
import { timeAverageAtom } from 'utils/state/atoms';
import { HiOutlineArrowDownTray } from 'react-icons/hi2';

type Props = {
  translationKey: string;
};

export function ChartTitle({ translationKey }: Props) {
  const { __, i18n } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);

  const localExists = i18n.exists(`${translationKey}.${timeAverage}`, {
    fallbackLng: i18n.language,
  });
  const localDefaultExists = i18n.exists(`${translationKey}.default`, {
    fallbackLng: i18n.language,
  });
  /*
  Use local for timeAverage if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <>
      <h3 className="pt-3 pb-1 text-md">
        {localExists
          ? __(`${translationKey}.${timeAverage}`)
          : __(
              `${translationKey}.default`,
              formatTimeRange(localDefaultExists ? i18n.language : 'en', timeAverage)
            )}
      </h3>
      <div className=" flex flex-row items-center pb-2 text-center text-sm  ">
        <HiOutlineArrowDownTray className="min-w-[12px]" size={12} />
        <a
          href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=country_panel"
          target="_blank"
          rel="noreferrer"
          className="whitespace-nowrap pl-0.5 text-sky-600 no-underline hover:underline  dark:invert"
        >
          {__('country-history.Getdata')}
        </a>
      </div>
    </>
  );
}
