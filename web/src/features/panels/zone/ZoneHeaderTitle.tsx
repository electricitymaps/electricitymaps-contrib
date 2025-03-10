import { CountryFlag } from 'components/Flag';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { Info } from 'lucide-react';
import { memo } from 'react';
import { getCountryName, getZoneName } from 'translation/translation';

import { getDisclaimer } from './util';

const MAX_TITLE_LENGTH = 25;

function ZoneHeaderTitle({
  zoneId,
  zoneNameFull,
}: {
  zoneId: string;
  zoneNameFull: string;
}) {
  const zoneName = getZoneName(zoneId);
  const showTooltip = zoneName !== zoneNameFull || zoneName.length >= MAX_TITLE_LENGTH;
  const countryName = getCountryName(zoneId);
  const disclaimer = getDisclaimer(zoneId);
  const showCountryPill =
    zoneId.includes('-') && !zoneName.toLowerCase().includes(countryName.toLowerCase());

  return (
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
        <h1 className="truncate" data-testid="zone-name">
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
  );
}

export default memo(ZoneHeaderTitle);
