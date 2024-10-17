import { CountryFlag } from 'components/Flag';
import { TimeDisplay } from 'components/TimeDisplay';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { useFeatureFlag } from 'features/feature-flags/api';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useSetAtom } from 'jotai';
import { ArrowLeft, Info } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { getCountryName, getFullZoneName, getZoneName } from 'translation/translation';
import { ZoneKey } from 'types';
import { baseUrl, metaTitleSuffix } from 'utils/constants';
import { createToWithState } from 'utils/helpers';

import { ShareButton } from './ShareButton';
import { getDisclaimer } from './util';

interface ZoneHeaderTitleProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
}

const MAX_TITLE_LENGTH = 25;

function getCurrentUrl({ zoneId }: { zoneId: ZoneKey }) {
  const url = baseUrl + (zoneId ? `/zone/${zoneId}` : '/map');
  return url;
}

export default function ZoneHeaderTitle({ zoneId }: ZoneHeaderTitleProps) {
  const zoneName = getZoneName(zoneId);
  const zoneNameFull = getFullZoneName(zoneId);
  const showTooltip = zoneName !== zoneNameFull || zoneName.length >= MAX_TITLE_LENGTH;
  const returnToMapLink = createToWithState('/map');
  const countryName = getCountryName(zoneId);
  const disclaimer = getDisclaimer(zoneId);
  const showCountryPill =
    zoneId.includes('-') && !zoneName.toLowerCase().includes(countryName.toLowerCase());
  const setIsMapMoving = useSetAtom(mapMovingAtom);
  const canonicalUrl = useGetCanonicalUrl();
  const isShareButtonEnabled = useFeatureFlag('share-button');

  const onNavigateBack = () => setIsMapMoving(false);
  const shareUrl = getCurrentUrl({ zoneId });

  return (
    <div className="flex w-full items-center pl-2 pr-3 pt-2">
      <Helmet prioritizeSeoTags>
        <title>{zoneName + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>
      <Link
        className="self-center py-4 pr-4 text-xl"
        to={returnToMapLink}
        data-test-id="left-panel-back-button"
        onClick={onNavigateBack}
      >
        <ArrowLeft />
      </Link>

      <div className="w-full overflow-hidden">
        <div className="flex w-full items-center gap-2 pr-2 md:pr-4">
          <CountryFlag
            zoneId={zoneId}
            size={18}
            className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
          />
          <TooltipWrapper
            tooltipContent={showTooltip ? zoneNameFull : undefined}
            side="bottom"
          >
            <h1 className="truncate" data-test-id="zone-name">
              {zoneName}
            </h1>
          </TooltipWrapper>
          {showCountryPill && (
            <div className="flex w-auto items-center rounded-full bg-gray-200 px-2 py-0.5 text-sm dark:bg-gray-800/80">
              <p className="w-full truncate">{countryName ?? zoneId}</p>
            </div>
          )}
          {disclaimer && (
            <TooltipWrapper side="bottom" tooltipContent={disclaimer}>
              <Info className="text-gray-500" />
            </TooltipWrapper>
          )}
        </div>
        <TimeDisplay className="whitespace-nowrap text-sm" />
      </div>
      {isShareButtonEnabled && <ShareButton shareUrl={shareUrl} />}
    </div>
  );
}
