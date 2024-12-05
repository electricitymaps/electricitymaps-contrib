import Logo from 'features/header/Logo';
import MobileButtons from 'features/map-controls/MobileButtons';
import { useAtom } from 'jotai';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Outlet, useLocation } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { useIsMobile } from 'utils/styling';

import { leftPanelOpenAtom } from './panelAtoms';

type CollapseButtonProps = {
  isCollapsed: boolean;
  onCollapse: () => void;
};

function CollapseButton({ isCollapsed, onCollapse }: CollapseButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      data-testid="left-panel-collapse-button"
      className={
        'absolute left-full top-2 z-[21] mt-[env(safe-area-inset-top)] h-12 w-6 cursor-pointer rounded-r bg-zinc-50 shadow-[6px_2px_10px_-3px_rgba(0,0,0,0.1)] hover:bg-zinc-100 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800'
      }
      onClick={onCollapse}
      aria-label={
        isCollapsed ? t('aria.label.showSidePanel') : t('aria.label.hideSidePanel')
      }
    >
      {isCollapsed ? <ChevronRight /> : <ChevronLeft />}
    </button>
  );
}

function MobileHeader() {
  return (
    <div className="flex w-full items-center justify-between pl-1 dark:bg-gray-900">
      <Logo className="h-10 w-44 fill-black dark:fill-white" />
      <MobileButtons />
    </div>
  );
}

function OuterPanel({ children }: { children: React.ReactNode }) {
  const [isOpen, setOpen] = useAtom(leftPanelOpenAtom);
  const location = useLocation();
  const isMobile = useIsMobile();

  const onCollapse = () => setOpen(!isOpen);

  return (
    <div
      data-testid="left-panel"
      className={twMerge(
        'absolute left-0 top-0 z-[21] h-full w-full bg-zinc-50 pt-[env(safe-area-inset-top)] shadow-xl transition-all duration-500 dark:bg-gray-900 dark:[color-scheme:dark] sm:w-[calc(14vw_+_16rem)]',
        location.pathname.startsWith('/map') ? 'hidden sm:flex' : 'block sm:flex',
        !isOpen && '-translate-x-full'
      )}
    >
      {isMobile && <MobileHeader />}
      <section className="h-full w-full">{children}</section>
      <CollapseButton isCollapsed={!isOpen} onCollapse={onCollapse} />
    </div>
  );
}

export default function LeftPanel() {
  return (
    <OuterPanel>
      <Outlet />
    </OuterPanel>
  );
}
