import useGetZone from 'api/getZone';
import HorizontalDivider from 'components/HorizontalDivider';
import { FormattedTime } from 'components/Time';
import { RoundedCard } from 'features/charts/RoundedCard';
import { useAtomValue } from 'jotai';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FiAlertTriangle, FiInfo } from 'react-icons/fi';
import i18n from 'translation/i18n';
import { TimeRange } from 'utils/constants';
import {
  isFiveMinuteOrHourlyGranularityAtom,
  selectedDatetimeIndexAtom,
  useTimeRangeSync,
} from 'utils/state/atoms';

export default function CurrentGridAlertsCard() {
  const { data, isLoading } = useGetZone();
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const [selectedTimeRange, _] = useTimeRangeSync();
  const isFineGranularity = useAtomValue(isFiveMinuteOrHourlyGranularityAtom);
  const { t } = useTranslation();

  const zoneMessage = data?.zoneMessage;
  const icon = getAlertIcon(zoneMessage?.alert_type ?? 'default');
  const colorClass = getAlertColorClass(zoneMessage?.alert_type ?? 'default');
  const [title, ...rest] = zoneMessage?.message.split('\n') ?? [];
  const text = rest.join('\n');
  const isLongMessage = text.length > 100;
  const [isCollapsed, setIsCollapsed] = useState(true);

  if (
    isLoading ||
    !zoneMessage ||
    !isFineGranularity ||
    zoneMessage.message_type !== 'grid_alert'
  ) {
    return null;
  }

  const startTime = new Date(zoneMessage.start_time ?? '');
  if (selectedTimeRange === TimeRange.H72) {
    startTime.setMinutes(0, 0, 0);
  } else {
    // set minutes to the closest 5 minutes in the past
    const minutes = startTime.getMinutes();
    const closest5Minutes = Math.round(minutes / 5) * 5;
    startTime.setMinutes(closest5Minutes, 0, 0);
  }
  if (selectedDatetime.datetime < startTime) {
    return null;
  }

  return (
    <RoundedCard className="gap-2 py-3 text-sm text-neutral-600 dark:text-neutral-300">
      <div className="flex flex-row items-center gap-1">
        {icon}{' '}
        <span className={`line-clamp-1 font-semibold ${colorClass}`} title={title}>
          {title}
        </span>
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
      {!isLongMessage && <div className="font-normal">{parseTextWithLinks(text)}</div>}
      {isLongMessage && (
        <div className="flex flex-col gap-1">
          <div className={`text-wrap font-normal ${isCollapsed ? 'line-clamp-2' : ''}`}>
            {parseTextWithLinks(text)}
          </div>
          <div className="items-left flex flex-row gap-1">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="font-semibold text-brand-yellow underline underline-offset-2 dark:text-brand-green-dark"
            >
              {isCollapsed
                ? t('grid-alerts-card.show-more')
                : t('grid-alerts-card.show-less')}
            </button>
          </div>
        </div>
      )}
    </RoundedCard>
  );
}

// Helper to parse text and replace URLs in parentheses with styled links
function parseTextWithLinks(text: string) {
  const urlRegex = /\((https?:\/\/[^)]+)\)/g;
  const parts: (string | JSX.Element)[] = [];
  let lastIndex = 0;
  let match;
  let key = 0;
  while ((match = urlRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const url = match[1];
    // Truncate: show only domain (or first 30 chars if no domain)
    let display = url;
    try {
      const { hostname } = new URL(url);
      display = hostname;
    } catch {
      display = url.slice(0, 30) + (url.length > 30 ? '...' : '');
    }
    parts.push(
      <a
        key={`link-${key++}`}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
      >
        {display}
      </a>
    );
    lastIndex = match.index + match[0].length;
  }
  // Push remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

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
