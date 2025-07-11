import useGetZone from 'api/getZone';
import HorizontalDivider from 'components/HorizontalDivider';
import { FormattedTime } from 'components/Time';
import { RoundedCard } from 'features/charts/RoundedCard';
import { useAtomValue } from 'jotai';
import { FiAlertTriangle, FiInfo } from 'react-icons/fi';
import i18n from 'translation/i18n';
import { TimeRange } from 'utils/constants';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';

const getAlertIcon = (alertType: string) => {
  if (alertType === 'action') {
    return (
      <FiAlertTriangle className="inline text-warning dark:text-warning-dark" size={16} />
    );
  }
  if (alertType === 'informational') {
    return <FiInfo className="inline" size={16} />;
  }
};

const getAlertColorClass = (alertType: string) => {
  if (alertType === 'action') {
    return 'text-warning dark:text-warning-dark';
  }
  if (alertType === 'informational') {
    return 'text-secondary dark:text-secondary-dark';
  }
};

export default function CurrentGridAlertsCard() {
  const { data, isLoading } = useGetZone();
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);

  const zoneMessage = data?.zoneMessage;
  const icon = getAlertIcon(zoneMessage?.alert_type ?? 'default');
  const colorClass = getAlertColorClass(zoneMessage?.alert_type ?? 'default');
  const [title, ...rest] = zoneMessage?.message.split('\n') ?? [];

  if (isLoading || !zoneMessage) {
    return null;
  }
  const startHour = new Date(zoneMessage.start_time ?? '');
  startHour.setMinutes(0, 0, 0);
  if (selectedDatetime.datetime < startHour) {
    return null;
  }

  return (
    <RoundedCard className="flex flex-col items-center gap-2 py-3 text-sm text-neutral-600 dark:text-neutral-300">
      {isLoading ? (
        <p className="text-center">Loading grid alerts...</p>
      ) : (
        <div>
          <div className="flex flex-row items-center gap-1">
            {icon} <span className={`font-semibold ${colorClass}`}>{title}</span>
          </div>
          <div className="flex flex-row items-center gap-1 text-xs">
            <FormattedTime
              datetime={new Date(zoneMessage?.start_time ?? '')}
              language={i18n.languages[0]}
              timeRange={TimeRange.H72}
            />
            {zoneMessage?.end_time && (
              <div className="flex flex-row items-center gap-1">
                <div>-</div>
                <FormattedTime
                  datetime={new Date(zoneMessage.end_time ?? '')}
                  language={i18n.languages[0]}
                  timeRange={TimeRange.H72}
                />
              </div>
            )}
          </div>
          <HorizontalDivider />
          <div className="font-normal">{rest.join('\n')}</div>
        </div>
      )}
    </RoundedCard>
  );
}
