import React, { useState, useMemo, useEffect } from 'react';

import { useLocation, useHistory } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import { getZoneId } from '../helpers/router';
import { getValueAtPosition } from '../helpers/grib';
import { calculateLengthFromDimensions } from '../helpers/math';
import { getCenteredZoneViewport, getCenteredLocationViewport } from '../helpers/map';
import { debounce } from '../helpers/debounce';

import { useInterpolatedSolarData, useInterpolatedWindData } from '../hooks/layers';
import { useCo2ColorScale, useTheme } from '../hooks/theme';
import { dispatchApplication } from '../store';

import ZoneMap from '../components/zonemap';
import MapLayer from '../components/maplayer';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import ExchangeLayer from '../components/layers/exchangelayer';
import SolarLayer from '../components/layers/solarlayer';
import WindLayer from '../components/layers/windlayer';
import { getCO2IntensityByMode } from '../helpers/zonedata';

const debouncedReleaseMoving = debounce(() => {
  dispatchApplication('isMovingMap', false);
}, 200);

export default () => {
  const webGLSupported = useSelector((state) => (state as any).application.webGLSupported);
  const isHoveringExchange = useSelector((state) => (state as any).application.isHoveringExchange);
  const electricityMixMode = useSelector((state) => (state as any).application.electricityMixMode);
  const callerLocation = useSelector((state) => (state as any).application.callerLocation);
  const isLoadingMap = useSelector((state) => (state as any).application.isLoadingMap);
  const isEmbedded = useSelector((state) => (state as any).application.isEmbedded);
  const isMobile = useSelector((state) => (state as any).application.isMobile);
  const viewport = useSelector((state) => (state as any).application.mapViewport);
  const selectedZoneTimeIndex = useSelector((state) => (state as any).application.selectedZoneTimeIndex);
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
  const zones = useSelector((state) => (state as any).data.zones);
  const { __ } = useTranslation();
  const solarData = useInterpolatedSolarData();
  const windData = useInterpolatedWindData();
  const location = useLocation();
  const history = useHistory();
  const co2ColorScale = useCo2ColorScale();

  // TODO: Replace with useParams().zoneId once this component gets
  // put in the right render context and has this param available.
  const zoneId = getZoneId();
  const theme = useTheme();

  const [tooltipPosition, setTooltipPosition] = useState(null);
  const [tooltipZoneData, setTooltipZoneData] = useState(null);
  const [hasCentered, setHasCentered] = useState(false);

  // Center the map initially based on the focused zone and the user geolocation.
  useEffect(() => {
    if (!hasCentered) {
      if (zoneId) {
        console.log(`Centering on zone ${zoneId}`); // eslint-disable-line no-console
        dispatchApplication('mapViewport', getCenteredZoneViewport(zones[zoneId].geography));
        setHasCentered(true);
      } else if (callerLocation) {
        console.log(`Centering on browser location (${callerLocation})`); // eslint-disable-line no-console
        dispatchApplication('mapViewport', getCenteredLocationViewport(callerLocation));
        setHasCentered(true);
      }
    }
  }, [zones, zoneId, callerLocation, hasCentered]);

  const handleMapLoaded = () => {
    // Map loading is finished, lower the overlay shield with
    // a bit of delay to allow the background to render first.
    setTimeout(() => {
      dispatchApplication('isLoadingMap', false);
    }, 100);

    // Track and notify that WebGL is supported.
    dispatchApplication('webGLSupported', true);
  };

  const handleMapError = (e: any) => {
    console.error(e.error);
    // Map loading is finished, lower the overlay shield.
    dispatchApplication('isLoadingMap', false);

    // Disable the map and redirect to zones ranking.
    if (e.error === 'WebGL not supported') {
      dispatchApplication('webGLSupported', false);
      history.push({ pathname: '/ranking', search: location.search });
    }
  };

  const handleMouseMove = useMemo(
    () =>
      ({ longitude, latitude, x, y }: any) => {
        if (solarData) {
          dispatchApplication('solarColorbarValue', getValueAtPosition(longitude, latitude, solarData));
        }
        if (windData) {
          dispatchApplication(
            'windColorbarValue',
            calculateLengthFromDimensions(
              getValueAtPosition(longitude, latitude, windData && windData[0]),
              getValueAtPosition(longitude, latitude, windData && windData[1])
            )
          );
        }
        // @ts-expect-error TS(2345): Argument of type '{ x: any; y: any; }' is not assi... Remove this comment to see the full error message
        setTooltipPosition({ x, y });
      },
    [solarData, windData]
  );

  const handleSeaClick = useMemo(
    () => () => {
      history.push({ pathname: '/map', search: location.search });
    },
    [history, location]
  );

  const handleZoneClick = useMemo(
    () => (id: any) => {
      dispatchApplication('isLeftPanelCollapsed', false);
      history.push({ pathname: `/zone/${id}`, search: location.search });
    },
    [history, location]
  );

  const handleZoneMouseEnter = useMemo(
    () => (zoneId: any) => {
      const zoneOverview = zones[zoneId][selectedTimeAggregate].overviews[selectedZoneTimeIndex];
      const zoneConfig = zones[zoneId].config;
      if (zoneOverview) {
        dispatchApplication('co2ColorbarValue', getCO2IntensityByMode(zoneOverview, electricityMixMode));
      }
      setTooltipZoneData({ ...zoneOverview, ...zoneConfig });
    },
    [electricityMixMode, selectedTimeAggregate, selectedZoneTimeIndex, zones]
  );

  const handleZoneMouseLeave = useMemo(
    () => () => {
      dispatchApplication('co2ColorbarValue', null);
      setTooltipZoneData(null);
    },
    []
  );

  const handleViewportChange = useMemo(
    () =>
      ({ width, height, latitude, longitude, zoom }: any) => {
        dispatchApplication('isMovingMap', true);
        dispatchApplication('mapViewport', {
          width,
          height,
          latitude,
          longitude,
          zoom,
        });
        // TODO: Try tying this to internal map state
        // somehow to remove the need for debouncing.
        debouncedReleaseMoving();
      },
    []
  );

  const handleResize = useMemo(
    () =>
      ({ width, height }: any) => {
        handleViewportChange({ ...viewport, width, height });
      },
    [viewport] // eslint-disable-line react-hooks/exhaustive-deps
  );

  // Animate map transitions only after the map has been loaded.
  const transitionDuration = isLoadingMap ? 0 : 300;
  const hoveringEnabled = !isHoveringExchange && !isMobile;

  return (
    <React.Fragment>
      <div id="webgl-error" className={`flash-message ${!webGLSupported ? 'active' : ''}`}>
        <div className="inner">{__('misc.webgl-not-supported')}</div>
      </div>
      {tooltipPosition && tooltipZoneData && hoveringEnabled && (
        <MapCountryTooltip
          isZoneNameDisplayed
          zoneData={tooltipZoneData}
          position={tooltipPosition}
          onClose={() => setTooltipZoneData(null)}
        />
      )}
      <ZoneMap
        co2ColorScale={co2ColorScale}
        hoveringEnabled={hoveringEnabled}
        onMapLoaded={handleMapLoaded}
        onMapError={handleMapError}
        onMouseMove={handleMouseMove}
        onResize={handleResize}
        onSeaClick={handleSeaClick}
        onViewportChange={handleViewportChange}
        onZoneClick={handleZoneClick}
        onZoneMouseEnter={handleZoneMouseEnter}
        onZoneMouseLeave={handleZoneMouseLeave}
        selectedZoneTimeIndex={selectedZoneTimeIndex}
        scrollZoom={!isEmbedded}
        theme={theme}
        transitionDuration={transitionDuration}
        viewport={viewport}
      >
        {/* @ts-expect-error TS(2322): Type 'NamedExoticComponent<object>' is not assigna... Remove this comment to see the full error message */}
        <MapLayer component={ExchangeLayer} />
        {/* @ts-expect-error TS(2322): Type '({ project, unproject }: any) => JSX.Element... Remove this comment to see the full error message */}
        <MapLayer component={WindLayer} />
        {/* @ts-expect-error TS(2322): Type '({ unproject }: any) => JSX.Element' is not ... Remove this comment to see the full error message */}
        <MapLayer component={SolarLayer} />
      </ZoneMap>
    </React.Fragment>
  );
};
