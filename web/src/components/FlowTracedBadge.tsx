import { ChevronsUp } from 'lucide-react';

import LabelTooltip from './tooltips/LabelTooltip';
import TooltipWrapper from './tooltips/TooltipWrapper';

export default function FlowTracedBadge(): JSX.Element {
  return (
    <TooltipWrapper
      side="bottom"
      tooltipContent={
        <LabelTooltip>
          Flow-traced data accounts for physical electricity flows
        </LabelTooltip>
      }
    >
      <div className="inline-flex h-6 min-w-[112px] items-center rounded-full bg-brand-green/10 px-2 py-1">
        <div className="flex flex-col">
          <ChevronsUp className="mr-1 h-4 w-4 font-semibold text-brand-green" />
        </div>
        <span className="text-xs font-semibold text-brand-green">Flow-traced</span>
      </div>
    </TooltipWrapper>
  );
}
