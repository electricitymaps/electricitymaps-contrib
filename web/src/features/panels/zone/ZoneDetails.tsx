import useGetZone from 'api/getZone';
import ApiButton from 'components/buttons/ApiButton';
import HorizontalDivider from 'components/HorizontalDivider';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import GenericPanel from 'features/panels/InterfacePanel';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useLocation, useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { Charts, SpatialAggregate } from 'utils/constants';
import { round } from 'utils/helpers';
import {
  displayByEmissionsAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

import AreaGraphContainer from './AreaGraphContainer';
import Attribution from './Attribution';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import EstimationCard from './EstimationCard';
import GridAlertsCard from './GridAlertsCard';
import MethodologyCard from './MethodologyCard';
import NoInformationMessage from './NoInformationMessage';
import { getHasSubZones, getZoneDataStatus, ZoneDataStatus } from './util';
import ZoneHeader from './ZoneHeader';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams<RouteParameters>();
  const timeRange = useAtomValue(timeRangeAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const setViewMode = useSetAtom(spatialAggregateAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const { data, isError, isLoading } = useGetZone();
  const { t } = useTranslation();
  const hasSubZones = getHasSubZones(zoneId);
  const isSubZone = zoneId ? zoneId.includes('-') : true;
  const zoneDataStatus = zoneId && getZoneDataStatus(zoneId, data);
  const selectedData = data?.zoneStates[selectedDatetimeString];
  const { estimationMethod, estimatedPercentage } = selectedData || {};
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationPillValue = // Renamed to avoid conflict with ZoneHeader prop if used directly
    Boolean(estimationMethod) || Boolean(roundedEstimatedPercentage);

  const trackEvent = useTrackEvent();
  const { trackCtaMiddle, trackCtaForecast } = useEvents(trackEvent);

  useEffect(() => {
    if (hasSubZones === null) {
      return;
    }
    if (hasSubZones && !isSubZone) {
      setViewMode(SpatialAggregate.COUNTRY);
    }
    if (!hasSubZones && isSubZone) {
      setViewMode(SpatialAggregate.ZONE);
    }
  }, [hasSubZones, isSubZone, setViewMode]);

  useScrollHashIntoView(isLoading);

  const datetimes = useMemo(
    () => Object.keys(data?.zoneStates || {})?.map((key) => new Date(key)),
    [data]
  );
  const zoneMessage = data?.zoneMessage;

  const zoneDetailsContent = useMemo(
    () =>
      zoneId &&
      zoneDataStatus && (
        <ZoneDetailsContentInternal zoneDataStatus={zoneDataStatus}>
          <BarBreakdownChart hasEstimationPill={hasEstimationPillValue} />
          {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && (
            <EstimationCard
              zoneKey={zoneId}
              zoneMessage={zoneMessage}
              estimatedPercentage={roundedEstimatedPercentage}
            />
          )}
          <ApiButton
            backgroundClasses="mt-3 mb-1"
            type="primary"
            onClick={trackCtaMiddle}
          />
          {zoneDataStatus === ZoneDataStatus.AVAILABLE && (
            <AreaGraphContainer
              datetimes={datetimes}
              timeRange={timeRange}
              displayByEmissions={displayByEmissions}
            />
          )}
          <GridAlertsCard
            datetimes={datetimes}
            timeRange={timeRange}
            displayByEmissions={displayByEmissions}
          />
          <MethodologyCard />
          <HorizontalDivider />
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold">{t('country-panel.forecastCta')}</div>
            <ApiButton size="sm" onClick={trackCtaForecast} />
          </div>
          <Attribution zoneId={zoneId} />
        </ZoneDetailsContentInternal>
      ),
    [
      zoneId,
      zoneDataStatus,
      hasEstimationPillValue,
      zoneMessage,
      roundedEstimatedPercentage,
      datetimes,
      timeRange,
      displayByEmissions,
      t,
      trackCtaForecast,
      trackCtaMiddle,
    ]
  );

  if (!zoneId) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }
  if (Array.isArray(data)) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  const panelError = isError ? t('country-panel.zoneerror') : null;

  const isEstimatedForHeader = Boolean(estimationMethod);

  return (
    <GenericPanel
      renderFullHeader={() => (
        <ZoneHeader zoneId={zoneId} isEstimated={isEstimatedForHeader} />
      )}
      headerHeight="64px"
      isLoading={isLoading && !data}
      error={panelError}
      contentClassName="px-3 pb-32 pt-2.5 sm:pb-4"
    >
      {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && <DisplayByEmissionToggle />}
      {zoneDetailsContent}
    </GenericPanel>
  );
}

function ZoneDetailsContentInternal({
  children,
  zoneDataStatus,
}: {
  children: React.ReactNode;
  zoneDataStatus: ZoneDataStatus | false;
}): JSX.Element {
  if (zoneDataStatus === ZoneDataStatus.NO_INFORMATION || zoneDataStatus == false) {
    return <NoInformationMessage />;
  }

  return children as JSX.Element;
}

const useScrollHashIntoView = (isLoading: boolean) => {
  const { hash, pathname, search } = useLocation();
  const anchor = hash.toLowerCase();

  useEffect(() => {
    if (isLoading) {
      return;
    }
    const chartIds = Object.values<string>(Charts);
    const anchorId = anchor.slice(1).toLowerCase();
    if (anchor && chartIds.includes(anchorId)) {
      const anchorElement = anchor ? document.querySelector(anchor) : null;
      if (anchorElement) {
        anchorElement.scrollIntoView({
          behavior: 'smooth',
          inline: 'nearest',
        });
      }
    } else {
      const element = document.querySelector('#generic-panel-scroller');
      if (element) {
        element.scrollTop = 0;
      }
    }
  }, [anchor, isLoading, pathname, search]);
};
