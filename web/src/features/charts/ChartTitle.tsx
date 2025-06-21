import { MoreOptionsDropdown } from 'components/MoreOptionsDropdown';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useGetCurrentUrl } from 'hooks/useGetCurrentUrl';
import { Ellipsis } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Charts, TimeRange } from 'utils/constants';
import { getDateRange } from 'utils/formatting';

type Props = {
  titleText?: string;
  unit?: string;
  badge?: React.ReactElement;
  className?: string;
  isEstimated?: boolean;
  id: Charts;
  subtitle?: React.ReactElement;
  isMoreOptionsHidden?: boolean;
};

export function ChartTitle({
  titleText,
  unit,
  badge,
  className,
  isEstimated,
  id,
  subtitle,
  isMoreOptionsHidden,
}: Props) {
  const showMoreOptions = useFeatureFlag('more-options-dropdown') && !isMoreOptionsHidden;
  const url = useGetCurrentUrl();
  const shareUrl = id ? `${url}#${id}` : url;
  const { t } = useTranslation();

  return (
    <div className="flex flex-col pb-2">
      <div className={`flex items-center gap-1.5 pt-4 ${className}`}>
        <h2 id={id} className="grow">
          {titleText}
        </h2>
        {badge}
        {showMoreOptions && (
          <MoreOptionsDropdown
            title={t(($) => $['more-options-dropdown']['chart-title'])}
            isEstimated={isEstimated}
            id={id}
            shareUrl={shareUrl}
          >
            <Ellipsis />
          </MoreOptionsDropdown>
        )}
      </div>
      <div className="flex flex-row items-center justify-between">
        {subtitle}
        {unit && (
          <div className="ml-auto text-xs text-[#8b8b8b] dark:text-[#848484]">{unit}</div>
        )}
      </div>
    </div>
  );
}

interface ChartSubtitleProps {
  datetimes: Date[];
  timeRange: TimeRange;
}

export function ChartSubtitle({ datetimes, timeRange }: ChartSubtitleProps) {
  const { i18n } = useTranslation();
  return (
    <p className="text-xs text-neutral-600 dark:text-neutral-300">
      {getDateRange(i18n.languages[0], datetimes, timeRange)}
    </p>
  );
}
