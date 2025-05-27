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
    <SidebarMenuItem className="flex flex-row justify-center">
      <SidebarMenuButton
        asChild
        className="gap-1.5 p-2 text-neutral-600 transition-all duration-200 hover:bg-[#126945]/10 hover:text-[#126945] data-[active=true]:bg-[#126945]/10 data-[active=true]:font-semibold data-[active=true]:text-[#126945] group-data-[collapsible=icon]:!p-1.5 dark:text-neutral-200 dark:hover:bg-[#4DC18C]/20 dark:hover:text-[#4DC18C] dark:data-[active=true]:bg-[#4DC18C]/20 dark:data-[active=true]:text-[#4DC18C] group-data-[collapsible=icon]:[&>svg]:size-5"
        isActive={isActive}
        onClick={trackNavigationClick}
      >
        <a href={to} className="flex flex-col">
          <Icon
            height={24}
            width={24}
            className="transition-[height,width] duration-200"
          />
          <div className="min-h-4 text-center text-[10px] leading-3">{label}</div>
        </a>
      </SidebarMenuButton>
      <div
        id={`sidebar-menu-item-${label.toLowerCase().replaceAll(' ', '_')}`}
        className="-translate-x-1.5"
      />
    </SidebarMenuItem>
  );
}
