import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import { getZoneTimezone } from 'utils/helpers';

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
  const { zoneId: pathZoneId } = useParams<RouteParameters>();
  const timeZoneZoneId = zoneId || pathZoneId;
  const timezone = getZoneTimezone(timeZoneZoneId);
  return (
    <time dateTime={datetime.toISOString()} className={className}>
      {formatDate(datetime, language, timeAverage, timezone)}
    </time>
  );
}
