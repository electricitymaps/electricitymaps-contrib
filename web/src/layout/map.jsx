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
import { useZonesWithColors } from '../hooks/map';
import { useFeatureToggle } from '../hooks/router';
import { dispatchApplication } from '../store';

import ZoneMap from '../components/zonemap';
import MapLayer from '../components/maplayer';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import ExchangeLayer from '../components/layers/exchangelayer';
import SolarLayer from '../components/layers/solarlayer';
import WindLayer from '../components/layers/windlayer';

const debouncedReleaseMoving = debounce(() => {
  dispatchApplication('isMovingMap', false);
}, 200);

export default () => {
  const webGLSupported = useSelector((state) => state.application.webGLSupported);
  const isHoveringExchange = useSelector((state) => state.application.isHoveringExchange);
  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);
  const callerLocation = useSelector((state) => state.application.callerLocation);
  const isLoadingMap = useSelector((state) => state.application.isLoadingMap);
  const isEmbedded = useSelector((state) => state.application.isEmbedded);
  const isMobile = useSelector((state) => state.application.isMobile);
  const viewport = useSelector((state) => state.application.mapViewport);
  const selectedZoneTimeIndex = useSelector((state) => state.application.selectedZoneTimeIndex);
  const zoneHistories = useSelector((state) => state.data.histories);
  const { __ } = useTranslation();
  const solarData = useInterpolatedSolarData();
  const windData = useInterpolatedWindData();
  const zones = useZonesWithColors();
  const location = useLocation();
  const history = useHistory();
  const co2ColorScale = useCo2ColorScale();
  const isHistoryFeatureEnabled = useFeatureToggle('history');

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
        dispatchApplication('mapViewport', getCenteredZoneViewport(zones[zoneId]));
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

  const handleMapError = (e) => {
    console.error(e.error);
    // Map loading is finished, lower the overlay shield.
    dispatchApplication('isLoadingMap', false);

    // Disable the map and redirect to zones ranking.
    dispatchApplication('webGLSupported', false);
    history.push({ pathname: '/ranking', search: location.search });
  };

  const handleMouseMove = useMemo(
    () =>
      ({ longitude, latitude, x, y }) => {
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
    () => (id) => {
      dispatchApplication('isLeftPanelCollapsed', false);
      history.push({ pathname: `/zone/${id}`, search: location.search });
    },
    [history, location]
  );

  const handleZoneMouseEnter = useMemo(
    () => (zoneId) => {
      const zoneHistoryDetails = zoneHistories?.[zoneId]?.[selectedZoneTimeIndex];
      const data = zoneHistoryDetails || zones[zoneId];
      dispatchApplication(
        'co2ColorbarValue',
        electricityMixMode === 'consumption' ? data.co2intensity : data.co2intensityProduction
      );
      setTooltipZoneData(data);
    },
    [electricityMixMode, zoneHistories, selectedZoneTimeIndex, zones]
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
      ({ width, height, latitude, longitude, zoom }) => {
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
      ({ width, height }) => {
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
          zoneData={tooltipZoneData}
          position={tooltipPosition}
          onClose={() => setTooltipZoneData(null)}
        />
      )}
      <ZoneMap
        co2ColorScale={co2ColorScale}
        hoveringEnabled={hoveringEnabled}
        isHistoryFeatureEnabled={isHistoryFeatureEnabled}
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
        zones={zones}
        zoomInLabel={__('tooltips.zoomIn')}
        zoomOutLabel={__('tooltips.zoomOut')}
        zoneHistories={zoneHistories}
      >
        <MapLayer component={ExchangeLayer} />
        <MapLayer component={WindLayer} />
        <MapLayer component={SolarLayer} />
      </ZoneMap>
    </React.Fragment>
  );
};
