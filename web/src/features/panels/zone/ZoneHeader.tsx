import DownloadCsv from 'components/buttons/DownloadCsv';
import { MoreOptionsDropdown, useShowMoreOptions } from 'components/MoreOptionsDropdown';
import { TimeDisplay } from 'components/TimeDisplay';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useGetCurrentUrl } from 'hooks/useGetCurrentUrl';
import { useAtomValue } from 'jotai';
import { Ellipsis } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { getFullZoneName, getSEOZoneName } from 'translation/translation';
import { metaTitleSuffix } from 'utils/constants';
import { isConsumptionAtom } from 'utils/state/atoms';

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
  const isConsumption = useAtomValue(isConsumptionAtom);

  const shareUrl = useGetCurrentUrl();
  const showMoreOptions = useShowMoreOptions();
  const { t } = useTranslation();

  return (
    <div className="flex w-full items-center pl-2 pr-3 sm:pt-2">
      <Helmet prioritizeSeoTags>
        <title>{seoZoneName + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>
      <ZoneHeaderBackButton />

      <div className="w-full overflow-hidden">
        <ZoneHeaderTitle zoneId={zoneId} zoneNameFull={zoneNameFull} />
        <TimeDisplay className="whitespace-nowrap text-sm" />
      </div>
      <DownloadCsv />
      {isShareButtonEnabled &&
        isConsumption &&
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
