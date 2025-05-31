import { CountryFlag } from 'components/Flag';
import LabelTooltip from 'components/tooltips/LabelTooltip';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { DataCenterIcon } from 'features/data-centers/DataCenterIcons';
import { Info } from 'lucide-react';
import { memo } from 'react';

import { getDisclaimer } from '../panels/zone/util';

const MAX_TITLE_LENGTH = 19;

function DataCenterHeaderTitle({
  zoneId,
  zoneNameFull,
  customTitle,
  provider,
}: {
  zoneId: string;
  zoneNameFull: string;
  customTitle?: string;
  provider?: string;
}) {
  const displayName = customTitle || zoneNameFull;
  const showTooltip = displayName.length >= MAX_TITLE_LENGTH;
  const disclaimer = getDisclaimer(zoneId);

  return (
    <div className="flex w-full items-center gap-2 pr-2 md:pr-4">
      {provider ? (
        <DataCenterIcon provider={provider} withPin={false} />
      ) : (
        <CountryFlag
          zoneId={zoneId}
          size={18}
          className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
        />
      )}
      <TooltipWrapper
        tooltipContent={
          showTooltip ? (
            <LabelTooltip className="max-w-[400px]">{displayName}</LabelTooltip>
          ) : undefined
        }
        side="bottom"
      >
        <h1 className="truncate" data-testid="data-center-name">
          {displayName}
        </h1>
      </TooltipWrapper>
      {disclaimer && (
        <TooltipWrapper
          side="bottom"
          tooltipContent={<LabelTooltip>{disclaimer}</LabelTooltip>}
        >
          <Info size={20} className="min-h-5 min-w-5 text-neutral-500" />
        </TooltipWrapper>
      )}
    </div>
  );
}

export default memo(DataCenterHeaderTitle);
