import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { FormattedTime } from 'components/Time';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { selectedDatetimeIndexAtom, timeRangeAtom } from 'utils/state/atoms';

export default function TimeHeader() {
  const { t, i18n } = useTranslation();
  const timeRange = useAtomValue(timeRangeAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  return (
    <div className="flex min-h-6 flex-row items-center">
      <h3 className="grow select-none text-left">
        {t(`time-controller.title.${timeRange}`)}
      </h3>
      {!isLoading && (
        <Badge
          pillText={
            <FormattedTime
              datetime={selectedDatetime.datetime}
              language={i18n.languages[0]}
              timeRange={timeRange}
            />
          }
          type="success"
        />
      )}
    </div>
  );
}
