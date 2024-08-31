import { Info } from "lucide-react";

import TooltipWrapper from "./tooltips/TooltipWrapper";

interface InfoIconWithTooltipProps {
  tooltipContent: string | JSX.Element;
}

export default function InfoIconWithTooltip({tooltipContent}: InfoIconWithTooltipProps) {
  return (
    <div className="absolute top-[58px] rounded-full bg-zinc-50 dark:bg-gray-900">
      <TooltipWrapper tooltipContent={tooltipContent} side="bottom">
        <Info className="p-1 text-brand-green" />
      </TooltipWrapper>
    </div>
  );
}