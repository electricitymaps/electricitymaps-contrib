import useGetZone from 'api/getZone';
import HorizontalDivider from 'components/HorizontalDivider';
import { useEffect, useState } from 'react';
import { FiAlertTriangle } from 'react-icons/fi';

interface ZoneAlert {
  message: string;
  start_time: string;
  end_time: string | null;
  alert_type: 'action' | 'informational' | string;
}

interface ZoneDetail {
  zoneMessage: ZoneAlert | null;
}

export default function CurrentGridAlertsCard() {
  const [zoneDetails, setZoneDetails] = useState<ZoneDetail[]>([]);
  const [loading, setLoading] = useState(true);

  const { data, isLoading: isZoneLoading } = useGetZone();

  useEffect(() => {
    async function fetchAlerts() {
      if (!data) {
        return;
      }

      setLoading(true);
      try {
        const zoneMessage = data.zoneMessage || null;

        if (zoneMessage) {
          setZoneDetails([{ zoneMessage }]);
        } else {
          setZoneDetails([]);
        }
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

  // Return nothing if not loading and no alerts
  if (!isLoading && zoneDetails.length === 0) {
    return null;
  }

  // If there are alerts, show the card
  return (
    <section>
      <div
        className={`mb-2 rounded-2xl border ${
          zoneDetails.some((z) => z.zoneMessage?.alert_type === 'action')
            ? 'border-warning bg-warning/10 dark:border-warning/60 dark:bg-warning/20'
            : 'border-neutral-200 bg-white/60 dark:border-neutral-700/80 dark:bg-neutral-800/60'
        } p-0`}
      >
        <div className="flex flex-col items-center gap-2 rounded-2xl bg-sunken p-4 dark:bg-sunken-dark">
          {isLoading ? (
            <p className="text-center text-xs">Loading grid alerts...</p>
          ) : (zoneDetails.length === 0 ? null : ( // Nothing shown when no alerts, or you can add a placeholder if you want
            <ul className="w-full">
              {zoneDetails.map(({ zoneMessage }, index) =>
                zoneMessage ? (
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
                      <FiAlertTriangle className="inline" />{' '}
                      {zoneMessage.message.split('\n')[0]}
                    </div>
                    <div
                      style={{
                        justifyContent: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        fontSize: 12,
                        fontFamily: 'Inter',
                        fontWeight: '400',
                        lineHeight: 4,
                        wordWrap: 'break-word',
                      }}
                    >
                      From: {zoneMessage.start_time}
                      {zoneMessage.end_time && <> &mdash; To: {zoneMessage.end_time}</>}
                    </div>
                    <div className="flex items-center justify-between font-bold">
                      <span className="text-xs uppercase opacity-70">
                        {zoneMessage.alert_type}
                      </span>
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
                      {zoneMessage.message.split('\n').slice(1).join('\n')}
                    </div>
                  </li>
                ) : null
              )}
            </ul>
          ))}
        </div>
      </div>
    </section>
  );
}
