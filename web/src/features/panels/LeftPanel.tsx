import GlassContainer from 'components/GlassContainer';
import Logo from 'components/Logo';
import MobileButtons from 'features/map-controls/MobileButtons';
import TimeControllerWrapper from 'features/time/TimeControllerWrapper';
import { Outlet, useLocation } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { useIsMobile } from 'utils/styling';

function MobileHeader() {
  return (
    <div className="flex w-full items-center justify-between pl-1 dark:bg-neutral-900">
      <Logo className="h-10 w-44 fill-black dark:fill-white" />
      <MobileButtons />
    </div>
  );
}

function OuterPanel({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const isMobile = useIsMobile();

  return (
    <div
      data-testid="left-panel"
      className={twMerge(
        'absolute inset-0 z-10 hidden sm:w-[calc(14vw_+_16rem)]',
        location.pathname.startsWith('/map') ? 'hidden sm:flex' : 'block sm:flex'
      )}
    >
      <GlassContainer className="z-[21] flex h-full flex-col pt-[env(safe-area-inset-top)] transition-all duration-500 sm:inset-3 sm:bottom-48 sm:h-auto">
        {isMobile && <MobileHeader />}
        <section className="flex flex-1 flex-col overflow-hidden">{children}</section>
      </GlassContainer>
      <TimeControllerWrapper />
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
