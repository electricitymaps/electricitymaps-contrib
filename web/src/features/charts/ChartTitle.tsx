import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { formatTimeRange } from 'utils/formatting';
import { timeAverageAtom } from 'utils/state/atoms';

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
    <h3 className="text-md">
      {localExists
        ? __(`${translationKey}.${timeAverage}`)
        : __(
            `${translationKey}.default`,
            formatTimeRange(localDefaultExists ? i18n.language : 'en', timeAverage)
          )}
    </h3>
  );
}
