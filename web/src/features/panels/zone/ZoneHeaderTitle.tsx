import { CountryFlag } from 'components/Flag';
import FlowTracedBadge from 'components/FlowTracedBadge';
import LabelTooltip from 'components/tooltips/LabelTooltip';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { Info } from 'lucide-react';
import { memo } from 'react';
import { getZoneName } from 'translation/translation';

import { getDisclaimer } from './util';

const MAX_TITLE_LENGTH = 10;

function ZoneHeaderTitle({
  zoneId,
  zoneNameFull,
}: {
  zoneId: string;
  zoneNameFull: string;
}) {
  const zoneName = getZoneName(zoneId);
  const showTooltip = zoneName !== zoneNameFull || zoneName.length >= MAX_TITLE_LENGTH;
  const disclaimer = getDisclaimer(zoneId);

  return (
    <div className="flex w-full items-center gap-2 pr-2 md:pr-4">
      <CountryFlag
        zoneId={zoneId}
        size={18}
        className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
      />
      <TooltipWrapper
        tooltipContent={
          showTooltip ? (
            <LabelTooltip className="max-w-[400px]">{zoneNameFull}</LabelTooltip>
          ) : undefined
        }
        side="bottom"
      >
        <h1 className="truncate" data-testid="zone-name">
          {zoneName}
        </h1>
      </TooltipWrapper>
      <FlowTracedBadge />
      {disclaimer && (
        <TooltipWrapper
          side="bottom"
          tooltipContent={<LabelTooltip>{disclaimer}</LabelTooltip>}
        >
          <Info className="min-h-6 min-w-6 text-neutral-500" />
        </TooltipWrapper>
      )}
    </div>
  );
}

export default memo(ZoneHeaderTitle);
