import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import type { LucideIcon } from 'lucide-react';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

import { SidebarMenuButton, SidebarMenuItem } from './Sidebar';

export function MenuItem({
  to,
  Icon,
  label,
  isActive = false,
}: {
  to: string;
  Icon: LucideIcon;
  label: string;
  isActive?: boolean;
}) {
  const handleClick = () => {
    trackEvent(TrackEvent.SIDEBAR_LINK_CLICKED, { linkId: label });
  };

  return (
    <TooltipWrapper
      tooltipContent={<p>{label}</p>}
      side="right"
      sideOffset={4}
      tooltipClassName=" bg-white z-50 py-1.5 px-3 "
    >
      <SidebarMenuItem className="flex flex-col">
        <SidebarMenuButton
          asChild
          className="p-2 text-neutral-600 transition-all duration-200 hover:bg-[#126945]/10 hover:text-[#126945] data-[active=true]:bg-[#126945]/10 data-[active=true]:font-semibold data-[active=true]:text-[#126945] group-data-[collapsible=icon]:!p-1.5 dark:text-[#E6E6E6] dark:data-[active=true]:text-[#126945] group-data-[collapsible=icon]:[&>svg]:size-5"
          isActive={isActive}
          onClick={handleClick}
        >
          <a href={to}>
            <Icon className="transition-[height,width] duration-200" />
            <span>{label}</span>
          </a>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </TooltipWrapper>
  );
}
