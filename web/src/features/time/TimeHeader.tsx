import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { NewFeaturePopover } from 'components/NewFeaturePopover/NewFeaturePopover';
import { NewFeaturePopoverContent } from 'components/NewFeaturePopover/NewFeaturePopoverContent';
import { FormattedTime } from 'components/Time';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export default function TimeHeader() {
  const { t, i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();
  return (
    <div className="flex min-h-6 flex-row items-center">
      <h3 className="grow select-none text-left">
        {t(`time-controller.title.${timeAverage}`)}
      </h3>
      {!isLoading && (
        <NewFeaturePopover
          side="top"
          content={<NewFeaturePopoverContent />}
          portal={false}
        >
          <Badge
            pillText={
              <FormattedTime
                datetime={selectedDatetime.datetime}
                language={i18n.languages[0]}
                timeAverage={timeAverage}
              />
            }
            type="success"
          />
        </NewFeaturePopover>
      )}
    </div>
  );
}
