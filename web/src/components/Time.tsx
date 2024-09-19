import { TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';

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
  return (
    <time dateTime={datetime.toISOString()} className={className}>
      {formatDate(datetime, language, timeAverage)}
    </time>
  );
}
