import Logo from 'components/Logo';
import TimeControllerWrapper from 'features/time/TimeControllerWrapper';
import { Outlet, useLocation } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';

function MapMobileHeader() {
  return (
    <div className="flex w-full items-center justify-between bg-gradient-to-b to-transparent px-2 pb-4 pt-safe dark:from-black/60">
      <Logo className="h-10 w-44  fill-black dark:fill-white" />
    </div>
  );
}
function OuterPanel({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <>
      <div className={`absolute left-0 right-0 top-0 z-20 sm:hidden`}>
        <MapMobileHeader />
      </div>
      <div
        data-testid="left-panel"
        className={twMerge(
          'pointer-events-none absolute inset-0 z-10  sm:w-[calc(14vw_+_16rem)]',
          location.pathname.startsWith('/map') ? 'hidden sm:flex' : 'block sm:flex'
        )}
      >
        {children}
        <TimeControllerWrapper />
      </div>
    </>
  );
}

export default function LeftPanel() {
  return (
    <OuterPanel>
      <Outlet />
    </OuterPanel>
  );
}
