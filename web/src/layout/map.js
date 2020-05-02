import React, {
  useState,
  useMemo,
  useRef,
  useEffect,
} from 'react';
import { useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { debounce, isEmpty, noop } from 'lodash';

import thirdPartyServices from '../services/thirdparty';
import { getZoneId, navigateTo } from '../helpers/router';
import { getValueAtPosition } from '../helpers/grib';
import { calculateLengthFromDimensions } from '../helpers/math';
import { getCenteredZoneViewport, getCenteredLocationViewport } from '../helpers/map';
import { useInterpolatedSolarData, useInterpolatedWindData } from '../hooks/layers';
import { useCo2ColorScale, useTheme } from '../hooks/theme';
import { useZonesWithColors } from '../hooks/map';
import { dispatchApplication } from '../store';

import ZoneMap from '../components/zonemap';
import MapLayer from '../components/maplayer';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import ExchangeLayer from '../components/layers/exchangelayer';
import SolarLayer from '../components/layers/solarlayer';
import WindLayer from '../components/layers/windlayer';

export default () => {
  const isHoveringExchange = useSelector(state => state.application.isHoveringExchange);
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);
  const callerLocation = useSelector(state => state.application.callerLocation);
  const isDraggingMap = useSelector(state => state.application.isDraggingMap);
  const isLoadingMap = useSelector(state => state.application.isLoadingMap);
  const isEmbedded = useSelector(state => state.application.isEmbedded);
  const isMobile = useSelector(state => state.application.isMobile);
  const viewport = useSelector(state => state.application.mapViewport);
  const zones = useZonesWithColors();
  const location = useLocation();
  // TODO: Replace with useParams().zoneId once this component gets
  // put in the right render context and has this param available.
  const zoneId = getZoneId();

  const solarData = useInterpolatedSolarData();
  const windData = useInterpolatedWindData();
  const theme = useTheme();

  const [tooltipPosition, setTooltipPosition] = useState(null);
  const [tooltipZoneData, setTooltipZoneData] = useState(null);

  const handleMapLoaded = useMemo(
    () => () => {
      // Center the map initially based on the focused zone and the user geolocation.
      if (zoneId) {
        console.log(`Centering on zone ${zoneId}`);
        dispatchApplication('mapViewport', getCenteredZoneViewport(zones[zoneId]));
      } else if (callerLocation) {
        console.log(`Centering on browser location (${callerLocation})`);
        dispatchApplication('mapViewport', getCenteredLocationViewport(callerLocation));
      }

      // Map loading is finished, lower the overlay shield.
      dispatchApplication('isLoadingMap', false);

      // Track and notify that WebGL is supported.
      dispatchApplication('webGLSupported', true);
      if (thirdPartyServices._ga) {
        thirdPartyServices._ga.timingMark('map_loaded');
      }
    },
    [zones, zoneId, callerLocation],
  );

  const handleMapInitFailed = useMemo(
    () => () => {
      // Map loading is finished, lower the overlay shield.
      dispatchApplication('isLoadingMap', false);

      // Redirect and notify that WebGL is not supported.
      dispatchApplication('webGLSupported', false);
      navigateTo({ pathname: '/ranking', search: location.search });
    },
    [],
  );

  const handleMouseMove = useMemo(
    () => ({
      longitude,
      latitude,
      x,
      y,
    }) => {
      dispatchApplication(
        'solarColorbarValue',
        getValueAtPosition(longitude, latitude, solarData),
      );
      dispatchApplication(
        'windColorbarValue',
        calculateLengthFromDimensions(
          getValueAtPosition(longitude, latitude, windData && windData[0]),
          getValueAtPosition(longitude, latitude, windData && windData[1]),
        ),
      );
      setTooltipPosition({ x, y });
    },
    [solarData, windData],
  );

  const handleSeaClick = useMemo(
    () => () => {
      navigateTo({ pathname: '/map', search: location.search });
    },
    [location],
  );

  const handleZoneClick = useMemo(
    () => (id) => {
      dispatchApplication('isLeftPanelCollapsed', false);
      navigateTo({ pathname: `/zone/${id}`, search: location.search });
      thirdPartyServices.trackWithCurrentApplicationState('countryClick');
    },
    [location],
  );

  const handleZoneMouseEnter = useMemo(
    () => (data, id) => {
      dispatchApplication(
        'co2ColorbarValue',
        electricityMixMode === 'consumption'
          ? data.co2intensity
          : data.co2intensityProduction
      );
      setTooltipZoneData(data);
    },
    [electricityMixMode],
  );

  const handleZoneMouseLeave = useMemo(
    () => () => {
      dispatchApplication('co2ColorbarValue', null);
      setTooltipZoneData(null);
    },
    [],
  );

  const debouncedSetNoDragging = useMemo(
    () => debounce(() => {
      dispatchApplication('isDraggingMap', false);
    }, 200),
    [],
  );

  const handleViewportChange = useMemo(
    () => ({ latitude, longitude, zoom }) => {
      dispatchApplication('isDraggingMap', true);
      dispatchApplication('mapViewport', { latitude, longitude, zoom });
      debouncedSetNoDragging();
    },
    [],
  );

  const hoveringEnabled = !isHoveringExchange && !isMobile;
  const transitionDuration = (isLoadingMap || isDraggingMap) ? 0 : 300;

  return (
    <React.Fragment>
      {tooltipPosition && tooltipZoneData && hoveringEnabled && (
        <MapCountryTooltip
          zoneData={tooltipZoneData}
          position={tooltipPosition}
        />
      )}
      <ZoneMap
        hoveringEnabled={hoveringEnabled}
        onMapLoaded={handleMapLoaded}
        onMapInitFailed={handleMapInitFailed}
        onMouseMove={handleMouseMove}
        onSeaClick={handleSeaClick}
        onViewportChange={handleViewportChange}
        onZoneClick={handleZoneClick}
        onZoneMouseEnter={handleZoneMouseEnter}
        onZoneMouseLeave={handleZoneMouseLeave}
        scrollZoom={!isEmbedded}
        theme={theme}
        transitionDuration={transitionDuration}
        viewport={viewport}
        zones={zones}
      >
        <MapLayer component={ExchangeLayer} />
        <MapLayer component={WindLayer} />
        <MapLayer component={SolarLayer} />
      </ZoneMap>
    </React.Fragment>
  );
};
