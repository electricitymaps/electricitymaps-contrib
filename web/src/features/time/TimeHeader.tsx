import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { NewFeaturePopover } from 'components/NewFeaturePopover';
import { FormattedTime } from 'components/Time';
import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtom, useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

import {
  DatePickerFeaturePopoverContent,
  newDatePickerDismissedAtom,
} from './DatePickerFeaturePopoverContent';

export default function TimeHeader() {
  const { t, i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const [isDismissed, setIsDismissed] = useAtom(newDatePickerDismissedAtom);
  const { isLoading: isLoadingData } = useGetState();
  const [isLoadingMap] = useAtom(loadingMapAtom);

  const allLoaded = !isLoadingMap && !isLoadingData;

  const onPopoverDismiss = () => setIsDismissed(true);

  return (
    <div className="flex min-h-6 flex-row items-center">
      <h3 className="grow select-none text-left">
        {t(`time-controller.title.${timeAverage}`)}
      </h3>
      {allLoaded && (
        <NewFeaturePopover
          isOpen={!isDismissed}
          onDismiss={onPopoverDismiss}
          side="top"
          content={<DatePickerFeaturePopoverContent />}
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
