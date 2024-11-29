import { CountryFlag } from 'components/Flag';
import { MoreOptionsDropdown, useShowMoreOptions } from 'components/MoreOptionsDropdown';
import { TimeDisplay } from 'components/TimeDisplay';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { useFeatureFlag } from 'features/feature-flags/api';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useGetCurrentUrl } from 'hooks/useGetCurrentUrl';
import { useAtomValue, useSetAtom } from 'jotai';
import { ArrowLeft, Ellipsis, Info } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import {
  getCountryName,
  getFullZoneName,
  getSEOZoneName,
  getZoneName,
} from 'translation/translation';
import { metaTitleSuffix } from 'utils/constants';
import { useNavigateWithParameters } from 'utils/helpers';
import { isConsumptionAtom } from 'utils/state/atoms';

import { ShareButton } from './ShareButton';
import { getDisclaimer } from './util';

interface ZoneHeaderTitleProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
}

const MAX_TITLE_LENGTH = 25;

export default function ZoneHeaderTitle({ zoneId, isEstimated }: ZoneHeaderTitleProps) {
  const zoneName = getZoneName(zoneId);
  const seoZoneName = getSEOZoneName(zoneId);
  const zoneNameFull = getFullZoneName(zoneId);
  const showTooltip = zoneName !== zoneNameFull || zoneName.length >= MAX_TITLE_LENGTH;
  const navigate = useNavigateWithParameters();

  const countryName = getCountryName(zoneId);
  const disclaimer = getDisclaimer(zoneId);
  const showCountryPill =
    zoneId.includes('-') && !zoneName.toLowerCase().includes(countryName.toLowerCase());
  const setIsMapMoving = useSetAtom(mapMovingAtom);
  const canonicalUrl = useGetCanonicalUrl();
  const isShareButtonEnabled = useFeatureFlag('share-button');
  const isConsumption = useAtomValue(isConsumptionAtom);

  const onNavigateBack = () => {
    setIsMapMoving(false);
    navigate({
      to: '/map',
    });
  };
  const shareUrl = useGetCurrentUrl();
  const showMoreOptions = useShowMoreOptions();
  const { t } = useTranslation();

  return (
    <div className="flex w-full items-center pl-2 pr-3 pt-2">
      <Helmet prioritizeSeoTags>
        <title>{seoZoneName + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>
      <div
        className="self-center py-4 pr-4 text-xl"
        data-test-id="left-panel-back-button"
        onClick={onNavigateBack}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            onNavigateBack();
          }
        }}
      >
        <ArrowLeft />
      </div>

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
