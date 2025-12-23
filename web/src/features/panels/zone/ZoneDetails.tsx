import useGetZone from 'api/getZone';
import ApiButton from 'components/buttons/ApiButton';
import GlassContainer from 'components/GlassContainer';
import HorizontalDivider from 'components/HorizontalDivider';
import LoadingSpinner from 'components/LoadingSpinner';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import { Charts, SpatialAggregate, TimeRange } from 'utils/constants';
import {
  displayByEmissionsAtom,
  isFiveMinuteOrHourlyGranularityAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
  timeRangeAtom,
  zoneDetailsScrollHashAtom,
} from 'utils/state/atoms';

import AreaGraphContainer from './AreaGraphContainer';
import Attribution from './Attribution';
import CurrentGridAlertsCard from './CurrentGridAlertsCard';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import ExperimentalCard from './ExperimentalCard';
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
  const isFineGranularity = useAtomValue(isFiveMinuteOrHourlyGranularityAtom);
  const { data, isError, isLoading } = useGetZone();
  const { t } = useTranslation();
  const hasSubZones = getHasSubZones(zoneId);
  const isSubZone = zoneId ? zoneId.includes('-') : true;
  const zoneDataStatus = zoneId && getZoneDataStatus(zoneId, data);
  const selectedData = data?.zoneStates[selectedDatetimeString];
  const { estimationMethod } = selectedData || {};
  const hasEstimationOrAggregationPill = Boolean(estimationMethod) || !isFineGranularity;

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

  useUpdateHashOnScroll(isLoading, 'panel-scroller');
  useScrollHashIntoView(isLoading, 'panel-scroller');

  const datetimes = useMemo(
    () => Object.keys(data?.zoneStates || {})?.map((key) => new Date(key)),
    [data]
  );

  // We isolate the component which is independant of `selectedData`
  // in order to avoid re-rendering it needlessly
  const zoneDetailsContent = useMemo(
    () =>
      zoneId &&
      zoneDataStatus && (
        <ZoneDetailsContent
          isLoading={isLoading}
          isError={isError}
          zoneDataStatus={zoneDataStatus}
        >
          <CurrentGridAlertsCard />
          <BarBreakdownChart hasEstimationPill={hasEstimationOrAggregationPill} />
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
        </ZoneDetailsContent>
      ),
    [
      zoneId,
      zoneDataStatus,
      isLoading,
      isError,
      hasEstimationOrAggregationPill,
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
        <ZoneHeader zoneId={zoneId} isEstimated={false} />
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
          {timeRange === TimeRange.H24 && (
            <ExperimentalCard
              title={t('experiment.5min.title')}
              description={t('experiment.5min.description')}
            />
          )}
          {zoneDetailsContent}
        </div>
      </section>
    </GlassContainer>
  );
}

function ZoneDetailsContent({
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
const useScrollHashIntoView = (isLoading: boolean, containerId: string) => {
  //const { hash, pathname, search } = useLocation();
  //const anchor = hash.toLowerCase();
  const setZoneDetailsScrollHash = useSetAtom(zoneDetailsScrollHashAtom);
  const zoneDetailsScrollHash = useAtomValue(zoneDetailsScrollHashAtom);

  useEffect(() => {
    if (isLoading) {
      return;
    }
    const anchor = zoneDetailsScrollHash ? `#${zoneDetailsScrollHash}` : '';
    const chartIds = Object.values<string>(Charts);
    const anchorId = anchor.slice(1).toLowerCase(); // remove leading #

    const sectionIds = getSectionIds(chartIds, containerId);
    if (anchor && sectionIds.has(anchorId)) {
      // scroll to same element as previously scrolled to, if it exists on this zone's details
      const anchorElement = anchor ? document.querySelector(anchor) : null;
      if (anchorElement) {
        anchorElement.scrollIntoView({
          behavior: 'smooth',
          inline: 'nearest',
        });
      }
    } else {
      // If already scrolled to element, then reset scroll on re-navigation (i.e. clicking on new zone on map)
      const element = document.querySelector(`#${containerId}`);
      if (element) {
        setZoneDetailsScrollHash('');
        element.scrollTop = 0;
      }
    }
  }, [isLoading, containerId]); //removed anchor/scroll hash vars from deps else scrolling would run every time they changed
};

function useUpdateHashOnScroll(isLoading: boolean, containerId: string) {
  const sectionIds = Object.values<string>(Charts);
  const setZoneDetailsScrollHash = useSetAtom(zoneDetailsScrollHashAtom);
  useEffect(() => {
    const container = document.querySelector(`#${containerId}`);
    if (isLoading || !container) {
      return;
    }
    // monitor when elements enter or leave viewport
    const observer = new window.IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        // get visible elements, sorted by visibility area ratio
        if (visible.length > 0) {
          const id = visible[0].target.id;
          //window.history.replaceState(null, '', `#${id}`);
          setZoneDetailsScrollHash(id);
        }
      },
      { root: container }
    );

    for (const id of sectionIds) {
      const element = document.querySelector(`#${id}`);
      if (element) {
        observer.observe(element);
      }
    }

    return () => observer.disconnect();
  }, [isLoading, sectionIds, containerId, setZoneDetailsScrollHash]);
}

function getSectionIds(sectionIds: string[], containerId: string): Set<string> {
  const container = document.querySelector(`#${containerId}`);
  const observedIds = new Set<string>();
  if (!container) {
    return observedIds;
  }
  for (const id of sectionIds) {
    const element = document.querySelector(`#${id}`);
    if (element) {
      observedIds.add(id);
    }
  }
  return observedIds;
}
