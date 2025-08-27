import { MoreOptionsDropdown } from 'components/MoreOptionsDropdown';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useGetCurrentUrl } from 'hooks/useGetCurrentUrl';
import { Ellipsis } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { getFullZoneName, getSEOZoneName } from 'translation/translation';
import { metaTitleSuffix } from 'utils/constants';

import { ShareButton } from './ShareButton';
import ZoneHeaderBackButton from './ZoneHeaderBackButton';
import ZoneHeaderTitle from './ZoneHeaderTitle';

interface ZoneHeaderTitleProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
}

export default function ZoneHeader({ zoneId, isEstimated }: ZoneHeaderTitleProps) {
  const seoZoneName = getSEOZoneName(zoneId);
  const zoneNameFull = getFullZoneName(zoneId);

  const canonicalUrl = useGetCanonicalUrl();
  const isShareButtonEnabled = useFeatureFlag('share-button');

  const shareUrl = useGetCurrentUrl();
  const showMoreOptions = useFeatureFlag('more-options-dropdown');
  const { t } = useTranslation();

  return (
    <div className="flex w-full items-center pl-1 pr-4 pt-[calc(max(env(safe-area-inset-top),var(--safe-area-inset-top))-2rem)] sm:pt-2">
      <Helmet prioritizeSeoTags>
        <title>{seoZoneName + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>
      <ZoneHeaderBackButton />

      <div className="w-full overflow-hidden">
        <ZoneHeaderTitle zoneId={zoneId} zoneNameFull={zoneNameFull} />
      </div>

      {isShareButtonEnabled &&
        (showMoreOptions ? (
          <MoreOptionsDropdown
            id="zone"
            shareUrl={shareUrl}
            title={t(`more-options-dropdown.title`) + ` ${zoneNameFull}`}
            isEstimated={isEstimated}
          >
            <Ellipsis />
          </MoreOptionsDropdown>
        ) : (
          <ShareButton shareUrl={shareUrl} />
        ))}
    </div>
  );
}
