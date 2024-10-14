import { TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import { getZoneTimezone, useGetZoneFromPath } from 'utils/helpers';

export function FormattedTime({
  datetime,
  language,
  timeAverage,
  className,
  zoneId,
}: {
  datetime: Date;
  language: string;
  timeAverage: TimeAverages;
  className?: string;
  zoneId?: string;
}) {
  const pathZoneId = useGetZoneFromPath();
  const timeZoneZoneId = zoneId || pathZoneId;
  const timezone = getZoneTimezone(timeZoneZoneId);
  return (
    <time dateTime={datetime.toISOString()} className={className}>
      {formatDate(datetime, language, timeAverage, timezone)}
    </time>
  );
}
