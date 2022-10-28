import Head from 'components/Head';
import type { ReactElement } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import ZoneDetails from './ZoneDetails';

export default function ZonePanelPage(): ReactElement {
  const { zoneId } = useParams();

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  return (
    <>
      <Head title={zoneId} />
      <h1>{zoneId}</h1>
      <ZoneDetails zoneId={zoneId} />
    </>
  );
}
