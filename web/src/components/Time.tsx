import { useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { formatDate } from 'utils/formatting';
import { getZoneTimezone } from 'utils/helpers';
import { timeRangeAtom } from 'utils/state/atoms';

export function FormattedTime({
  datetime,
  language,
  className,
  zoneId,
  isTimeHeader = false,
  endDatetime,
}: {
  datetime: Date;
  language: string;
  className?: string;
  zoneId?: string;
  isTimeHeader?: boolean;
  endDatetime?: Date;
}) {
  const timeRange = useAtomValue(timeRangeAtom);
  const { zoneId: pathZoneId } = useParams<RouteParameters>();
  const timeZoneZoneId = zoneId || pathZoneId;
  const timezone = getZoneTimezone(timeZoneZoneId);
  return (
    <time dateTime={datetime.toISOString()} className={className}>
      {formatDate(datetime, language, timeRange, timezone, isTimeHeader, endDatetime)}
    </time>
  );
}
