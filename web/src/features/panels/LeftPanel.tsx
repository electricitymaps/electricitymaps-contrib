import { Button } from 'components/Button';
import LoadingSpinner from 'components/LoadingSpinner';
import Logo from 'features/header/Logo';
import MobileButtons from 'features/map-controls/MobileButtons';
import { useAtom, useAtomValue } from 'jotai';
import { ArrowLeftToLine, ArrowRightFromLine } from 'lucide-react';
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
import { useIsBiggerThanMobile, useIsMobile } from 'utils/styling';

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

function CollapseButton() {
  const { t } = useTranslation();
  const [leftPanelOpen, setLeftPanelOpen] = useAtom(leftPanelOpenAtom);
  const isBiggerThanMobile = useIsBiggerThanMobile();
  return (
    isBiggerThanMobile && (
      <Button
        data-test-id="left-panel-collapse-button"
        size="lg"
        type="secondary"
        backgroundClasses={`pointer-events-auto absolute left-full top-0 z-10 ml-2 bg-red-600 transition-all duration-500 ${
          leftPanelOpen ? '' : '-translate-x-[calc(500px+0.5rem)]'
        }`}
        onClick={() => setLeftPanelOpen(!leftPanelOpen)}
        icon={leftPanelOpen ? <ArrowLeftToLine /> : <ArrowRightFromLine />}
        aria-label={
          leftPanelOpen ? t('aria.label.hideSidePanel') : t('aria.label.showSidePanel')
        }
      />
    )
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
  const isOpen = useAtomValue(leftPanelOpenAtom);
  const location = useLocation();
  const isMobile = useIsMobile();

  return (
    !(location.pathname === '/map' && isMobile) && (
      <>
        <div
          data-test-id="left-panel"
          className={`pointer-events-auto relative z-20 w-full grow overflow-y-scroll bg-zinc-50  shadow-xl transition-all duration-500 dark:bg-gray-900 dark:[color-scheme:dark] ${
            location.pathname === '/map' && isMobile ? 'hidden' : ''
          } ${isOpen ? '' : '-translate-x-[calc(500px+0.5rem)]'}
          ${isMobile ? 'h-full' : 'rounded-2xl p-2'}`}
        >
          {isMobile && <MobileHeader />}
          {children}
        </div>
        <CollapseButton />
      </>
    )
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
