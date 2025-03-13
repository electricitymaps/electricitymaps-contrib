import { LogoIcon } from 'features/header/Logo';
import { BookOpenIcon, CodeXmlIcon, FileSpreadsheetIcon, MapIcon } from 'lucide-react';

import { MenuItem } from './MenuItem';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
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
    icon: FileSpreadsheetIcon,
  },
  {
    label: 'API',
    to: `${PORTAL_URL}`,
    icon: CodeXmlIcon,
  },
  {
    label: 'API Docs',
    to: `${PORTAL_URL}/docs`,
    icon: BookOpenIcon,
  },
];

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader>
        <div>
          <LogoIcon className="ml-2 size-8 text-black dark:text-white" />
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
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
      {/* <SidebarFooter>
          <div className="flex items-center justify-between gap-4 overflow-hidden transition-all duration-200 group-data-[collapsible=icon]:mb-6 group-data-[collapsible=icon]:items-start">
            <SupportButton label="Support" Icon={HelpCircleIcon} />
          </div>
        </SidebarFooter> */}
    </Sidebar>
  );
}
