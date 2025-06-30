import useGetZone from 'api/getZone';
import HorizontalDivider from 'components/HorizontalDivider';
import { useEffect, useState } from 'react';
import { FiAlertTriangle, FiInfo } from 'react-icons/fi';
import { ZoneMessage } from 'types';

interface ZoneDetail {
  zoneMessage: ZoneMessage | null;
}

// format date function to format date strings
const formatDate = (dateString?: string) => {
  if (!dateString) {
    return 'N/A';
  }
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
};

// Configuration for icons and colors based on alert type
const alertTypeConfig: Record<
  string,
  {
    icon: JSX.Element;
    colorClass: string;
  }
> = {
  action: {
    icon: <FiAlertTriangle className="inline" />,
    colorClass: 'bg-warning/10',
  },
  informational: {
    icon: <FiInfo className="inline" />,
    colorClass: 'text-neutral-600 dark:text-neutral-400',
  },
  default: {
    icon: <FiInfo className="inline" />,
    colorClass: 'text-neutral-600',
  },
};

export default function CurrentGridAlertsCard() {
  const [zoneDetails, setZoneDetails] = useState<ZoneDetail[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch zone details using the custom hook
  const { data, isLoading: isZoneLoading } = useGetZone();

  useEffect(() => {
    async function fetchAlerts() {
      if (!data) {
        return;
      }

      setLoading(true);
      try {
        const zoneMessage = data.zoneMessage || null;
        setZoneDetails(zoneMessage ? [{ zoneMessage }] : []);
      } catch (error) {
        console.error('Error fetching grid state or zone details:', error);
        setZoneDetails([]);
      } finally {
        setLoading(false);
      }
    }

    fetchAlerts();
  }, [data]);

  const isLoading = loading || isZoneLoading;

  // Nothing to show
  if (!isLoading && zoneDetails.length === 0) {
    return null;
  }

  // At least one alert action type
  const isAction = zoneDetails.some((z) => z.zoneMessage?.alert_type === 'action');

  return (
    <section>
      <div
        className={`mb-2 rounded-2xl border ${
          isAction
            ? 'border-warning bg-warning/10 dark:border-warning/60 dark:bg-warning/20'
            : 'border-neutral-200 bg-white/60 dark:border-neutral-700/80 dark:bg-neutral-800/60'
        } p-0`}
      >
        <div className="flex flex-col items-center gap-2 rounded-2xl bg-sunken p-4 dark:bg-sunken-dark">
          {isLoading ? (
            <p className="text-center text-xs">Loading grid alerts...</p>
          ) : (
            <ul className="w-full">
              {zoneDetails.map(({ zoneMessage }, index) => {
                if (!zoneMessage) {
                  return null;
                }

                const alertConfig = alertTypeConfig[zoneMessage.alert_type ?? 'default'];
                const [title, ...rest] = zoneMessage.message.split('\n');

                return (
                  <li
                    key={`${zoneMessage.start_time}-${
                      zoneMessage.end_time ?? 'no-end'
                    }-${index}`}
                    className={`mb-2 rounded-2xl ${
                      zoneMessage.alert_type === 'action' ? 'bg-warning/10' : 'bg-info/10'
                    } p-2`}
                  >
                    <div
                      style={{
                        flex: '1 1 0',
                        justifyContent: 'center',
                        flexDirection: 'column',
                        color: 'var(--status-warning, #B45309)',
                        fontSize: 14,
                        fontFamily: 'Inter',
                        fontWeight: '600',
                        wordWrap: 'break-word',
                      }}
                    >
                      {alertConfig.icon}{' '}
                      <span className={`font-semibold ${alertConfig.colorClass}`}>
                        {title}
                      </span>
                    </div>
                    <div
                      style={{
                        justifyContent: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        fontSize: 12,
                        fontFamily: 'Inter',
                        fontWeight: '400',
                        lineHeight: 2,
                        wordWrap: 'break-word',
                      }}
                    >
                      {formatDate(zoneMessage.start_time)}
                      {zoneMessage.end_time && (
                        <> &mdash; {formatDate(zoneMessage.end_time)}</>
                      )}
                    </div>
                    <HorizontalDivider />
                    <div
                      style={{
                        width: '100%',
                        justifyContent: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        fontSize: 14,
                        fontFamily: 'Inter',
                        fontWeight: '400',
                        wordWrap: 'break-word',
                      }}
                    >
                      {rest.join('\n')}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
