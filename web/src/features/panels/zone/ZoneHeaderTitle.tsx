import { Button } from 'components/Button';
import { CountryFlag } from 'components/Flag';
import { TimeDisplay } from 'components/TimeDisplay';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { useFeatureFlag } from 'features/feature-flags/api';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useAtomValue, useSetAtom } from 'jotai';
import { ArrowLeft, Info } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { getCountryName, getFullZoneName, getZoneName } from 'translation/translation';
import { ZoneKey } from 'types';
import { ShareType, trackShare } from 'utils/analytics';
import { baseUrl, metaTitleSuffix } from 'utils/constants';
import { createToWithState } from 'utils/helpers';
import { isHourlyAtom, selectedDatetimeStringAtom } from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

import { ShareButton } from './ShareButton';
import { getDisclaimer } from './util';

interface ZoneHeaderTitleProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
}

const MAX_TITLE_LENGTH = 25;

function generateCurrentSelectedDatetimeUrl({
  selectedDatetimeString,
  zoneId,
}: {
  selectedDatetimeString: string;
  zoneId: ZoneKey;
}) {
  const url =
    baseUrl + (zoneId ? `/zone/${zoneId}` : '/map') + `?${selectedDatetimeString}`;
  return url;
}

export default function ZoneHeaderTitle({ zoneId }: ZoneHeaderTitleProps) {
  const zoneName = getZoneName(zoneId);
  const zoneNameFull = getFullZoneName(zoneId);
  const showTooltip = zoneName !== zoneNameFull || zoneName.length >= MAX_TITLE_LENGTH;
  const returnToMapLink = createToWithState('/map');
  const countryName = getCountryName(zoneId);
  const disclaimer = getDisclaimer(zoneId);
  const showCountryPill = zoneId.includes('-') && !zoneName.includes(countryName);
  const setIsMapMoving = useSetAtom(mapMovingAtom);
  const canonicalUrl = useGetCanonicalUrl();
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const isShareButtonEnabled = useFeatureFlag('share-button');


  const onNavigateBack = () => setIsMapMoving(false);
  const isHourly = useAtomValue(isHourlyAtom);
  const isMobile = useIsMobile();

  const copyUrlToClipboard = async () => {
    const url = generateCurrentSelectedDatetimeUrl({ selectedDatetimeString, zoneId });
    trackShare(ShareType.ZONE);

    if (isMobile && navigator.canShare({ url })) {
      try {
        await navigator.share({ title: 'Electricity Maps', text: 'TODO', url: url });
      } catch (error) {
        console.error('Failed to share URL:', error);
      }
    } else {
      navigator.clipboard
        .writeText(url)
        .then(() => {
          alert('Copied to clipboard, TODO deploy the toast');
        })
        .catch((error) => {
          console.error('Failed to copy URL:', error);
        });
    }
  };
  return (
    <div className="flex w-full items-center pl-2 pr-3 pt-2">
      <Helmet prioritizeSeoTags>
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
          {isHourly && <Button onClick={copyUrlToClipboard}>Test</Button>}
        </div>
        <TimeDisplay className="whitespace-nowrap text-sm" />
      </div>
      {isShareButtonEnabled && <ShareButton />}
    </div>
  );
}
