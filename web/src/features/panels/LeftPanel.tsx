import { useState } from 'react';
import { HiChevronLeft, HiChevronRight } from 'react-icons/hi2';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import RankingPanel from './ranking-panel/RankingPanel';

import ZoneDetails from './zone/ZoneDetails';

function ValidZoneIdGuardWrapper({ children }: { children: JSX.Element }) {
  const { zoneId } = useParams();

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }
  return children;
}

type CollapseButtonProps = {
  isCollapsed: boolean;
  onCollapse: () => void;
};

// TODO: Add icon, handle hover state
function CollapseButton({ isCollapsed, onCollapse }: CollapseButtonProps) {
  return (
    <button
      data-test-id="left-panel-collapse-button"
      className={
        'absolute left-full top-2 z-10 h-12 w-6 cursor-pointer rounded-r bg-zinc-50 shadow-[6px_2px_10px_-3px_rgba(0,0,0,0.1)] dark:bg-gray-800'
      }
      onClick={onCollapse}
    >
      {isCollapsed ? <HiChevronLeft /> : <HiChevronRight />}
    </button>
  );
}

function OuterPanel({ children }: { children: React.ReactNode }) {
  const [isOpen, setOpen] = useState(true);
  const onCollapse = () => setOpen(!isOpen);

  return (
    <aside
      className={`absolute left-0 top-0 z-20 h-full w-full bg-zinc-50 shadow-xl transition-all duration-500 dark:bg-gray-800 dark:[color-scheme:dark] md:flex md:w-[calc(14vw_+_16rem)] ${
        !isOpen && '-translate-x-full'
      }`}
    >
      <section className="w-full overflow-y-scroll p-2">{children}</section>
      <CollapseButton isCollapsed={!isOpen} onCollapse={onCollapse} />
    </aside>
  );
}

export default function LeftPanel() {
  return (
    <OuterPanel>
      <Routes>
        <Route
          path="/zone/:zoneId"
          element={
            <ValidZoneIdGuardWrapper>
              <ZoneDetails />
            </ValidZoneIdGuardWrapper>
          }
        />
        <Route path="/faq" element={<p>FAQ</p>} />
        {/* Alternative: add /map here and have a NotFound component for anything else*/}
        <Route path="*" element={<RankingPanel />} />
      </Routes>
    </OuterPanel>
  );
}
