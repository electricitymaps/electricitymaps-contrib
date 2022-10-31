import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom';
import ZoneDetails from './Zone/ZoneDetails';

function ValidZoneIdGuardWrapper({ children }: { children: JSX.Element }): JSX.Element {
  const { zoneId } = useParams();

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function LeftPanel(): JSX.Element {
  return (
    <div className="left-panel">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<p>Ranking</p>} />
          <Route path="/map" element={<p>Ranking</p>} />
          <Route
            path="/zone/:zoneId"
            element={
              <ValidZoneIdGuardWrapper>
                <ZoneDetails />
              </ValidZoneIdGuardWrapper>
            }
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}
