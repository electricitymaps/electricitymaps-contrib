import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { formatDate, formatDateRange } from 'utils/formatting';
import { getZoneTimezone } from 'utils/helpers';

export function FormattedTime({
  datetime,
  language,
  timeRange,
  className,
  zoneId,
  endDatetime,
}: {
  datetime: Date;
  language: string;
  timeRange?: TimeRange;
  className?: string;
  zoneId?: string;
  endDatetime?: Date;
}) {
  const { zoneId: pathZoneId } = useParams<RouteParameters>();
  const timeZoneZoneId = zoneId || pathZoneId;
  const timezone = getZoneTimezone(timeZoneZoneId);
  if (timeRange) {
    return (
      <time dateTime={datetime.toISOString()} className={className}>
        {formatDate(datetime, language, timeRange, timezone)}
      </time>
    );
  }
  return (
    <time dateTime={datetime.toISOString()} className={className}>
      {endDatetime && formatDateRange(datetime, endDatetime, language, timezone)}
    </time>
  );
}
