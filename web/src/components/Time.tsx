import { TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';

export function FormattedTime({
  datetime,
  language,
  timeAverage,
}: {
  datetime: Date;
  language: string;
  timeAverage: TimeAverages;
}) {
  return (
    <time dateTime={datetime.toISOString()}>
      {formatDate(datetime, language, timeAverage)}
    </time>
  );
}
