import type { LucideIcon } from 'lucide-react';

import { MenuItem } from './MenuItem';

export function SupportButton({ Icon, label }: { Icon: LucideIcon; label: string }) {
  return <MenuItem to="https://help.electricitymaps.com/" Icon={Icon} label={label} />;
}
