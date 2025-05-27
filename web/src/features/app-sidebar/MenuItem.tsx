import LabelTooltip from 'components/tooltips/LabelTooltip';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { useNavigationEvent, useTrackEvent } from 'hooks/useTrackEvent';
import type { LucideIcon } from 'lucide-react';

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
  const trackEvent = useTrackEvent();
  const trackNavigationClick = useNavigationEvent(trackEvent, label);

  return (
    <div id={`sidebar-menu-item-${label.toLowerCase().replaceAll(' ', '_')}`}>
      <TooltipWrapper
        tooltipContent={<LabelTooltip>{label}</LabelTooltip>}
        side="right"
        sideOffset={4}
      >
        <SidebarMenuItem className="flex flex-col">
          <SidebarMenuButton
            asChild
            className="p-2 text-neutral-600 transition-all duration-200 hover:bg-[#126945]/10 hover:text-[#126945] data-[active=true]:bg-[#126945]/10 data-[active=true]:font-semibold data-[active=true]:text-[#126945] group-data-[collapsible=icon]:!p-1.5 dark:text-neutral-200 dark:hover:bg-[#4DC18C]/20 dark:hover:text-[#4DC18C] dark:data-[active=true]:bg-[#4DC18C]/20 dark:data-[active=true]:text-[#4DC18C] group-data-[collapsible=icon]:[&>svg]:size-5"
            isActive={isActive}
            onClick={trackNavigationClick}
          >
            <a href={to}>
              <Icon className="transition-[height,width] duration-200" />
              <span>{label}</span>
            </a>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </TooltipWrapper>
    </div>
  );
}
