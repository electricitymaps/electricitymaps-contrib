import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { LogoIcon } from 'components/Logo';
import LabelTooltip from 'components/tooltips/LabelTooltip';
import TooltipWrapper, {
  type TooltipWrapperReference,
} from 'components/tooltips/TooltipWrapper';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import {
  BookOpenIcon,
  ChartNoAxesCombined,
  CodeXmlIcon,
  FileDownIcon,
  HelpCircleIcon,
  MapIcon,
} from 'lucide-react';
import { useRef, useState } from 'react';

import { MenuItem } from './MenuItem';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from './Sidebar';

// Sidebar width is used in various places to calculate the view widths
export const SIDEBAR_WIDTH = '63px';

const PORTAL_URL = 'https://portal.electricitymaps.com';

const MENU_ITEMS = [
  {
    to: '/',
    label: 'Map',
    icon: MapIcon,
    isActive: true,
  },
  {
    label: 'Datasets',
    to: `${PORTAL_URL}/datasets`,
    icon: FileDownIcon,
  },
  {
    label: 'Data Explorer',
    to: `${PORTAL_URL}/data-explorer`,
    icon: ChartNoAxesCombined,
  },
  {
    label: 'API',
    to: `${PORTAL_URL}`,
    icon: CodeXmlIcon,
  },
  {
    label: 'Docs',
    to: `${PORTAL_URL}/docs`,
    icon: BookOpenIcon,
  },
];

export function AppSidebar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const tooltipReference = useRef<TooltipWrapperReference>(null);
  const isIntercomEnabled = useFeatureFlag('intercom-messenger');
  const trackEvent = useTrackEvent();
  const { trackSupportChat, trackSupportFaq } = useEvents(trackEvent);

  const handleOpenChange = (open: boolean) => {
    setIsMenuOpen(open);
    if (open) {
      tooltipReference.current?.close();
    }
  };

  const handleChat = () => {
    trackSupportChat();
    if (window.Intercom) {
      window.Intercom('show');
    } else {
      console.warn('Intercom not available');
    }
  };

  return (
    <Sidebar>
      <SidebarHeader>
        <div>
          <LogoIcon className="ml-4 size-4 text-black dark:text-white" />
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu className="group-data-[collapsible=icon]:gap-8">
            {MENU_ITEMS.map((item) => (
              <MenuItem
                key={item.to}
                to={item.to}
                label={item.label}
                Icon={item.icon}
                isActive={item.isActive || false}
              />
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <TooltipWrapper
          ref={tooltipReference}
          tooltipContent={
            isMenuOpen ? undefined : <LabelTooltip>Help & Support</LabelTooltip>
          }
          side="right"
          sideOffset={4}
        >
          <SidebarMenuItem className="flex flex-col">
            <DropdownMenu.Root open={isMenuOpen} onOpenChange={handleOpenChange}>
              <DropdownMenu.Trigger asChild>
                <SidebarMenuButton
                  className="p-2 text-neutral-600 transition-all duration-200 hover:bg-[#126945]/10 hover:text-[#126945] data-[active=true]:bg-[#126945]/10 data-[active=true]:font-semibold data-[active=true]:text-[#126945] group-data-[collapsible=icon]:!p-1.5 dark:text-neutral-200 dark:hover:bg-[#4DC18C]/20 dark:hover:text-[#4DC18C] dark:data-[active=true]:bg-[#4DC18C]/20 dark:data-[active=true]:text-[#4DC18C] group-data-[collapsible=icon]:[&>svg]:size-5"
                  aria-label="Help and Support Menu"
                >
                  <HelpCircleIcon />
                </SidebarMenuButton>
              </DropdownMenu.Trigger>

              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  className="z-50 min-w-[150px] rounded-md border border-neutral-200 bg-white p-1 text-sm text-neutral-700 shadow-md dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-200"
                  sideOffset={16}
                  side="right"
                  align="end"
                >
                  <DropdownMenu.Item asChild onSelect={trackSupportFaq}>
                    <a
                      href="https://help.electricitymaps.com/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 outline-none hover:bg-neutral-100 focus:bg-neutral-100 dark:hover:bg-neutral-700 dark:focus:bg-neutral-700"
                    >
                      FAQ & Support
                    </a>
                  </DropdownMenu.Item>
                  {isIntercomEnabled && (
                    <DropdownMenu.Item
                      onSelect={handleChat}
                      className="flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 outline-none hover:bg-neutral-100 focus:bg-neutral-100 dark:hover:bg-neutral-700 dark:focus:bg-neutral-700"
                    >
                      Chat With Us
                    </DropdownMenu.Item>
                  )}
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </SidebarMenuItem>
        </TooltipWrapper>
      </SidebarFooter>
    </Sidebar>
  );
}
