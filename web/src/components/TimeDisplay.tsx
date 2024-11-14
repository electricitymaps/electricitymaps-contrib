import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { ZoneKey } from 'types';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

import { FormattedTime } from './Time';

export function TimeDisplay({
  className,
  zoneId,
}: {
  className?: string;
  zoneId?: ZoneKey;
}) {
  const { i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);

  return (
    <FormattedTime
      datetime={selectedDatetime.datetime}
      language={i18n.languages[0]}
      timeAverage={timeAverage}
      className={className}
      zoneId={zoneId}
    />
  );
}
