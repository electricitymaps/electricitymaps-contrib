import LoadingSpinner from 'components/LoadingSpinner';
import Logo from 'features/header/Logo';
import MobileButtons from 'features/map-controls/MobileButtons';
import { useAtom } from 'jotai';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import { useIsMobile } from 'utils/styling';

import { leftPanelOpenAtom } from './panelAtoms';

const RankingPanel = lazy(() => import('./ranking-panel/RankingPanel'));
const ZoneDetails = lazy(() => import('./zone/ZoneDetails'));

function HandleLegacyRoutes() {
  const [searchParameters] = useSearchParams();

  const page = (searchParameters.get('page') || 'map')
    .replace('country', 'zone')
    .replace('highscore', 'ranking');
  searchParameters.delete('page');

  const zoneId = searchParameters.get('countryCode');
  searchParameters.delete('countryCode');

  return (
    <Navigate
      to={{
        pathname: zoneId ? `/zone/${zoneId}` : `/${page}`,
        search: searchParameters.toString(),
      }}
    />
  );
}

function ValidZoneIdGuardWrapper({ children }: { children: JSX.Element }) {
  const [searchParameters] = useSearchParams();
  const { zoneId } = useParams();

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  // Handle legacy Australia zone names
  if (zoneId.startsWith('AUS')) {
    return (
      <Navigate to={`/zone/${zoneId.replace('AUS', 'AU')}?${searchParameters}`} replace />
    );
  }
  const upperCaseZoneId = zoneId.toUpperCase();
  if (zoneId !== upperCaseZoneId) {
    return <Navigate to={`/zone/${upperCaseZoneId}?${searchParameters}`} replace />;
  }

  return children;
}

type CollapseButtonProps = {
  isCollapsed: boolean;
  onCollapse: () => void;
};

function CollapseButton({ isCollapsed, onCollapse }: CollapseButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      data-test-id="left-panel-collapse-button"
      className={
        'absolute left-full top-2 z-[21] h-12 w-6 cursor-pointer rounded-r bg-zinc-50 shadow-[6px_2px_10px_-3px_rgba(0,0,0,0.1)] hover:bg-zinc-100 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800'
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
    <div className="mt-[env(safe-area-inset-top)] flex w-full items-center justify-between pl-1 dark:bg-gray-900">
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
      data-test-id="left-panel"
      className={`absolute left-0 top-0 z-[21] h-full w-full bg-zinc-50 shadow-xl transition-all duration-500 dark:bg-gray-900 dark:[color-scheme:dark] sm:flex sm:w-[calc(14vw_+_16rem)] ${
        location.pathname === '/map' ? 'hidden' : ''
      } ${isOpen ? '' : '-translate-x-full'}`}
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
      <Routes>
        <Route path="/" element={<HandleLegacyRoutes />} />
        <Route
          path="/zone/:zoneId"
          element={
            <ValidZoneIdGuardWrapper>
              <Suspense fallback={<LoadingSpinner />}>
                <ZoneDetails />
              </Suspense>
            </ValidZoneIdGuardWrapper>
          }
        />
        {/* Alternative: add /map here and have a NotFound component for anything else*/}
        <Route
          path="*"
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <RankingPanel />
            </Suspense>
          }
        />
      </Routes>
    </OuterPanel>
  );
}
