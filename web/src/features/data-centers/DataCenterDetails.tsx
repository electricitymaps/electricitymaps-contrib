import useGetZone from 'api/getZone';
import GlassContainer from 'components/GlassContainer';
import HorizontalDivider from 'components/HorizontalDivider';
import LoadingSpinner from 'components/LoadingSpinner';
import { TimeDisplay } from 'components/TimeDisplay';
import CarbonChart from 'features/charts/CarbonChart';
import EmissionChart from 'features/charts/EmissionChart';
import OriginChart from 'features/charts/OriginChart';
import { RoundedCard } from 'features/charts/RoundedCard';
import DataCenterHeader from 'features/data-centers/DataCenterHeader';
import { dataCenters } from 'features/data-centers/DataCenterLayer';
import { ZoneHeaderGauges } from 'features/panels/zone/ZoneHeaderGauges';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Navigate, useLocation, useParams } from 'react-router-dom';
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

import Attribution from '../panels/zone/Attribution';
import DisplayByEmissionToggle from '../panels/zone/DisplayByEmissionToggle';
import EstimationCard from '../panels/zone/EstimationCard';
import MethodologyCard from '../panels/zone/MethodologyCard';
import NoInformationMessage from '../panels/zone/NoInformationMessage';
import { getHasSubZones, getZoneDataStatus, ZoneDataStatus } from '../panels/zone/util';

// NL/gcp/europe-west4
// TODO: look up zone name
// TODO: look up data center info

export default function DataCenterDetails(): JSX.Element {
  const { zoneId, provider, region, resolution, urlTimeRange, urlDatetime } =
    useParams<RouteParameters>();
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
  const { estimatedPercentage } = selectedData || {};
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);

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
          {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && (
            <EstimationCard
              zoneKey={zoneId}
              zoneMessage={zoneMessage}
              estimatedPercentage={roundedEstimatedPercentage}
            />
          )}
          {zoneDataStatus === ZoneDataStatus.AVAILABLE && (
            <>
              {displayByEmissions ? (
                <EmissionChart datetimes={datetimes} timeRange={timeRange} />
              ) : (
                <CarbonChart datetimes={datetimes} timeRange={timeRange} />
              )}
              <OriginChart
                displayByEmissions={displayByEmissions}
                datetimes={datetimes}
                timeRange={timeRange}
              />
            </>
          )}
          <RoundedCard>
            <div className="flex items-center gap-1 py-2">
              <h2>{t('Data Center Info')}</h2>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span>Parent zone:</span>
                <span>parent zone name</span>
              </div>
              <div className="flex justify-between">
                <span>Operating since:</span>
                <span>operating since</span>
              </div>
            </div>
            <HorizontalDivider />
            <p className="flex justify-between text-xs">
              <span>Source:</span>
              <span>tbd</span>
            </p>
          </RoundedCard>
          <MethodologyCard />
          <HorizontalDivider />
          <Attribution zoneId={zoneId} />
        </DataCenterDetailsContent>
      ),
    [
      zoneId,
      zoneDataStatus,
      isLoading,
      isError,
      zoneMessage,
      roundedEstimatedPercentage,
      datetimes,
      timeRange,
      displayByEmissions,
      t,
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
          {/* TODO: handle misisng link information */}
          <Link
            className="text-xs underline"
            to={`/zone/${zoneId}/${urlTimeRange}/${resolution}/${urlDatetime ?? ''}`}
          >
            See parent zone for more information
          </Link>
          <RoundedCard className="my-2 pb-4">
            <div className="flex flex-col py-2">
              <h2>{t('Overview')}</h2>
              <TimeDisplay className="whitespace-nowrap text-xs text-neutral-600 dark:text-neutral-300" />
            </div>
            <ZoneHeaderGauges zoneKey={zoneId} />
          </RoundedCard>
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
