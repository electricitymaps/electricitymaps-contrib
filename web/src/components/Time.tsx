import { TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import { getZoneTimeZone, useGetZoneFromPath } from 'utils/helpers';

export function FormattedTime({
  datetime,
  language,
  timeAverage,
  className,
}: {
  datetime: Date;
  language: string;
  timeAverage: TimeAverages;
  className?: string;
}) {
  const zoneId = useGetZoneFromPath();
  const timezone = getZoneTimeZone(zoneId);
  return (
    <time dateTime={datetime.toISOString()} className={className}>
      {formatDate(datetime, language, timeAverage, timezone)}
    </time>
  );
}
