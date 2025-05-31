import useGetZone from 'api/getZone';
import ApiButton from 'components/buttons/ApiButton';
import GlassContainer from 'components/GlassContainer';
import HorizontalDivider from 'components/HorizontalDivider';
import LoadingSpinner from 'components/LoadingSpinner';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import DataCenterHeader from 'features/data-centers/DataCenterHeader';
import { dataCenters } from 'features/data-centers/DataCenterLayer';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useLocation, useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import { Charts, SpatialAggregate } from 'utils/constants';
import { round } from 'utils/helpers';
import {
  displayByEmissionsAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

import AreaGraphContainer from '../panels/zone/AreaGraphContainer';
import Attribution from '../panels/zone/Attribution';
import DisplayByEmissionToggle from '../panels/zone/DisplayByEmissionToggle';
import EstimationCard from '../panels/zone/EstimationCard';
import GridAlertsCard from '../panels/zone/GridAlertsCard';
import MethodologyCard from '../panels/zone/MethodologyCard';
import NoInformationMessage from '../panels/zone/NoInformationMessage';
import { getHasSubZones, getZoneDataStatus, ZoneDataStatus } from '../panels/zone/util';

export default function DataCenterDetails(): JSX.Element {
  const { zoneId, provider, region } = useParams<RouteParameters>();
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
  const hasEstimationPill =
    Boolean(estimationMethod) || Boolean(roundedEstimatedPercentage);

  // Find the matching data center
  const dataCenterKey = useMemo(() => {
    if (!zoneId || !provider || !region) {
      return null;
    }
    return Object.keys(dataCenters).find(
      (key) =>
        dataCenters[key].zoneKey === zoneId &&
        dataCenters[key].provider === provider &&
        dataCenters[key].region === region
    );
  }, [zoneId, provider, region]);

  const dataCenterName = dataCenterKey
    ? dataCenters[dataCenterKey].displayName
    : undefined;

  const trackEvent = useTrackEvent();
  const { trackCtaMiddle, trackCtaForecast } = useEvents(trackEvent);

  useEffect(() => {
    if (hasSubZones === null) {
      return;
    }
    // When first hitting the map (or opening a zone from the search panel),
    // set the correct matching view mode (zone or country).
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

  // We isolate the component which is independent of `selectedData`
  // in order to avoid re-rendering it needlessly
  const dataCenterDetailsContent = useMemo(
    () =>
      zoneId &&
      zoneDataStatus && (
        <DataCenterDetailsContent
          isLoading={isLoading}
          isError={isError}
          zoneDataStatus={zoneDataStatus}
        >
          <BarBreakdownChart hasEstimationPill={hasEstimationPill} />
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
        </DataCenterDetailsContent>
      ),
    [
      zoneId,
      zoneDataStatus,
      isLoading,
      isError,
      hasEstimationPill,
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

  if (!zoneId || !provider || !region) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  // TODO: App-backend should not return an empty array as "data" if the zone does not
  // exist.
  if (Array.isArray(data)) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  return (
    <GlassContainer
      className={twMerge(
        'pointer-events-auto z-[21] flex h-full flex-col border-0 transition-all duration-500 sm:inset-3 sm:bottom-[8.5rem] sm:h-auto sm:border sm:pt-0',
        'pt-[max(2.5rem,env(safe-area-inset-top))] sm:pt-0' // use safe-area, keep sm:pt-0
      )}
    >
      <section className="h-full w-full">
        <DataCenterHeader
          zoneId={zoneId}
          isEstimated={false}
          customTitle={dataCenterName}
          provider={provider}
        />
        <div
          id="panel-scroller"
          className={twMerge(
            // TODO: Can we set the height here without using calc and specific zone-header value?
            'h-full flex-1 overflow-y-scroll px-3 pb-32 pt-2.5 sm:h-[calc(100%-64px)] sm:pb-4'
          )}
        >
          {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && (
            <DisplayByEmissionToggle />
          )}
          {dataCenterDetailsContent}
        </div>
      </section>
    </GlassContainer>
  );
}

function DataCenterDetailsContent({
  isLoading,
  isError,
  children,
  zoneDataStatus,
}: {
  isLoading: boolean;
  isError: boolean;
  children: React.ReactNode;
  zoneDataStatus: ZoneDataStatus;
}): JSX.Element {
  if (isLoading) {
    return (
      <div className="relative mt-[10vh]">
        <LoadingSpinner />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        data-testid="no-parser-message"
        className={`flex h-full w-full items-center justify-center text-sm`}
      >
        🤖 Unknown server error 🤖
      </div>
    );
  }

  if (zoneDataStatus === ZoneDataStatus.NO_INFORMATION) {
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
    const anchorId = anchor.slice(1).toLowerCase(); // remove leading #

    if (anchor && chartIds.includes(anchorId)) {
      const anchorElement = anchor ? document.querySelector(anchor) : null;
      if (anchorElement) {
        anchorElement.scrollIntoView({
          behavior: 'smooth',
          inline: 'nearest',
        });
      }
    } else {
      // If already scrolled to element, then reset scroll on re-navigation (i.e. clicking on new zone on map)
      const element = document.querySelector('#panel-scroller');
      if (element) {
        element.scrollTop = 0;
      }
    }
  }, [anchor, isLoading, pathname, search]);
};
