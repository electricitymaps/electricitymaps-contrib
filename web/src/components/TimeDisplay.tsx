import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { ZoneKey } from 'types';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';

import { FormattedTime } from './Time';

export function TimeDisplay({
  className,
  zoneId,
}: {
  className?: string;
  zoneId?: ZoneKey;
}) {
  const { i18n } = useTranslation();
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);

  return (
    <FormattedTime
      datetime={selectedDatetime.datetime}
      language={i18n.languages[0]}
      className={className}
      zoneId={zoneId}
    />
  );
}
