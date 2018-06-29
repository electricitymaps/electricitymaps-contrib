import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

export default class Map {
  _setupMapColor() {
    if (this.map.isStyleLoaded() && this.map.getLayer('clickable-zones-fill') && this.co2color) {
      const co2Range = this.theme.co2Scale.steps;
      const stops = co2Range.map(d => [d, this.co2color(d)]);
      this.map.setPaintProperty('clickable-zones-fill', 'fill-color', {
        default: this.theme.clickableFill,
        property: 'co2intensity',
        stops,
      });
      this.map.setPaintProperty('background', 'background-color', this.theme.oceanColor);
      this.map.setPaintProperty('zones-line', 'line-color', this.theme.strokeColor);
      this.map.setPaintProperty('zones-line', 'line-width', this.theme.strokeWidth);
    }
  }

  paintData() {
    if (!this.data) { return; }
    const clickableSource = this.map.getSource('clickable-world');
    const nonClickableSource = this.map.getSource('non-clickable-world');
    const clickableData = {
      type: 'FeatureCollection',
      features: this.clickableZoneGeometries,
    };
    const nonClickableData = {
      type: 'FeatureCollection',
      features: this.nonClickableZoneGeometries,
    };
    if (clickableSource && nonClickableSource) {
      clickableSource.setData(clickableData);
      nonClickableSource.setData(nonClickableData);
    } else if (this.map.isStyleLoaded()) {
      // Create sources
      this.map.addSource('clickable-world', {
        type: 'geojson',
        data: clickableData,
      });
      this.map.addSource('non-clickable-world', {
        type: 'geojson',
        data: nonClickableData,
      });
      this.map.addSource('hover', {
        type: 'geojson',
        data: clickableData, // Duplicating source makes filter operations faster https://github.com/mapbox/mapbox-gl-js/issues/5040#issuecomment-321688603
      });
      // Create layers
      const paint = {
        'fill-color': this.theme.clickableFill,
      };
      if (this.co2color) {
        const co2Range = [0, 200, 400, 600, 800, 1000];
        const stops = co2Range.map(d => [d, this.co2color(d)]);
        paint['fill-color'] = {
          stops,
          property: 'co2intensity',
          default: this.theme.clickableFill,
        };
      }
      this.map.addLayer({
        id: 'background',
        type: 'background',
        paint: { 'background-color': this.theme.oceanColor },
      });
      this.map.addLayer({
        id: 'clickable-zones-fill',
        type: 'fill',
        source: 'clickable-world',
        layout: {},
        paint,
      });
      this.map.addLayer({
        id: 'non-clickable-zones-fill',
        type: 'fill',
        source: 'non-clickable-world',
        layout: {},
        paint: { 'fill-color': this.theme.nonClickableFill },
      });
      this.map.addLayer({
        id: 'zones-hover',
        type: 'fill',
        source: 'hover',
        layout: {},
        paint: {
          'fill-color': 'white',
          'fill-opacity': 0.3,
        },
        filter:  ['==', 'zoneId', ''],
      });
      // Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer
      this.map.addLayer({
        id: 'zones-line',
        type: 'line',
        source: 'clickable-world',
        layout: {},
        paint: {
          'line-color': this.theme.strokeColor,
          'line-width': this.theme.strokeWidth,
        },
      });
    }
  }

  constructor(selectorId, argConfig) {
    const config = argConfig || {};
    const defaulttheme = {
      strokeWidth: 0.3,
      strokeColor: '#FAFAFA',
      clickableFill: '#D4D9DE',
      nonClickableFill: '#D4D9DE',
      oceanColor: '#FAFAFA',
      co2Scale: {
        steps: [0, 150, 600, 750],
        colors: ['#2AA364', '#F5EB4D', '#9E293E', '#1B0E01'],
      },
    };

    this.theme = argConfig.theme || defaulttheme;
    this.userIsUsingTouch = false;

    this.center = undefined;
    this.zoom = config.zoom;

    if (!mapboxgl.supported()) {
      throw 'WebGL not supported';
    }

    this.map = new mapboxgl.Map({
      container: selectorId, // selector id
      attributionControl: false,
      scrollZoom: true,
      style: {
        version: 8,
        sources: {},
        layers: [],
        zoom: this.zoom || 3,
        center: this.center || [0, 50],
      },
    });

    this.map.dragRotate.disable();
    this.map.touchZoomRotate.disableRotation();
    this.map.doubleClickZoom.disable(); /* Transform scale is not given properly when enabled */

    this.map.on('load', () => {
      // Here we need to set all styles
      this.paintData();
      this._setupMapColor();
      // For some reason the mapboxgl-canvas element sometimes has
      // the wrong size, so we resize it here just in case.
      this.map.resize();
    });

    // Set a timer to detect when the map has finished loading
    const loadingInterval = setInterval(() => {
      if (this.map.loaded()) {
        clearInterval(loadingInterval);
        // For some reason, setCenter/setZoom commands that are called too soon are ignored.
        if (this.center) { this.map.setCenter(this.center); }
        if (this.zoom) { this.map.setZoom(this.zoom); }
        this.mapLoadedHandlers.forEach(h => h(this));
      }
    }, 100);

    // Add zoom and rotation controls to the map.
    const navigationControlOptions = {
      showCompass: false,
    };
    this.map.addControl(new mapboxgl.NavigationControl(navigationControlOptions));

    this.dragStartHandlers = [];
    this.dragHandlers = [];
    this.dragEndHandlers = [];
    this.mapLoadedHandlers = [];

    this.map.on('touchstart', e => {
      // the user actually touched the screen!
      // he has a touch feature AND is using it. See #1090
      this.userIsUsingTouch = true;
      console.log('user is using touch');
    });

    this.map.on('mouseenter', 'clickable-zones-fill', (e) => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      this.map.getCanvas().style.cursor = 'pointer';
      if (this.countryMouseOverHandler) {
        const i = e.features[0].properties.zoneId;
        this.countryMouseOverHandler.call(this, this.data[i], i);
      }
    });

    let prevId;
    this.map.on('mousemove', 'clickable-zones-fill', (e) => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      const { zoneId } = e.features[0].properties;
      if (prevId !== zoneId) {
        prevId = zoneId;
        this.map.setFilter('zones-hover', ['==', 'zoneId', zoneId]);
      }
      if (this.zoneMouseMoveHandler) {
        this.zoneMouseMoveHandler.call(
          this,
          this.data[zoneId],
          zoneId,
          e.point.x,
          e.point.y,
        );
      }
    });
    this.map.on('mousemove', (e) => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      if (this.mouseMoveHandler) {
        const p = this.map.unproject([e.point.x, e.point.y]);
        this.mouseMoveHandler.call(
          this,
          [p.lng, p.lat],
        );
      }
    });
    this.map.on('mouseleave', 'clickable-zones-fill', () => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      this.map.getCanvas().style.cursor = '';
      this.map.setFilter('zones-hover', ['==', 'zoneId', '']);

      prevId = null;
      if (this.zoneMouseOutHandler) {
        this.zoneMouseOutHandler.call(this);
      }
    });
    this.map.on('click', (e) => {
      const features = this.map.queryRenderedFeatures(e.point);
      if (!features.length) {
        if (this.seaClickHandler) {
          this.seaClickHandler.call(this);
        }
      } else if (this.countryClickHandler) {
        const i = features[0].properties.zoneId;
        this.countryClickHandler.call(this, this.data[i], i);
      }
    });

    // *** PAN/ZOOM ***
    let dragInitialTransform;
    let dragStartTransform;
    let isDragging = false;
    let endTimeout = null;

    const onPanZoom = (e) => {
      if (endTimeout) {
        clearTimeout(endTimeout);
        endTimeout = null;
      }
      const transform = {
        x: e.target.transform.x,
        y: e.target.transform.y,
        k: e.target.transform.scale,
      };
      this.dragHandlers.forEach(h => h.call(this, transform));
    };

    const onPanZoomStart = (e) => {
      // For some reason, MapBox gives us many start events inside a single zoom.
      // Those apply for touch events on mobile
      // They are removed here:
      if (isDragging) { return; }
      if (endTimeout) {
        clearTimeout(endTimeout);
        endTimeout = null;
      } else {
        isDragging = true;
        const transform = {
          x: e.target.transform.x,
          y: e.target.transform.y,
          k: e.target.transform.scale,
        };
        if (!dragInitialTransform) {
          dragInitialTransform = transform;
        }
        if (!dragStartTransform) {
          dragStartTransform = transform;
        }
        this.dragStartHandlers.forEach(h => h.call(this, transform));
      }
    };

    const onPanZoomEnd = (e) => {
      // Move end fires many times during multitouch events, see
      // https://github.com/mapbox/mapbox-gl-js/issues/3435
      // therefore, we debounce it.
      if (!isDragging) { return; }
      if (!endTimeout) {
        endTimeout = setTimeout(() => {
          isDragging = false;
          this.dragEndHandlers.forEach(h => h.call(this));
          dragStartTransform = undefined;
          endTimeout = null;
        }, 50);
      }
    };

    this.map.on('move', onPanZoom);
    this.map.on('movestart', onPanZoomStart);
    this.map.on('moveend', onPanZoomEnd);

    return this;
  }

  setCo2color(arg, theme) {
    this.co2color = arg;
    this.theme = theme;
    this._setupMapColor();
    return this;
  }

  setTheme(arg) {
    this.theme = arg;
    this._setupMapColor();
    return this;
  }

  projection() {
    // Read-only property
    return (lonlat) => {
      const p = this.map.project(lonlat);
      return [p.x, p.y];
    };
  }

  unprojection() {
    // Read-only property
    return (xy) => {
      const p = this.map.unproject(xy);
      return [p.lng, p.lat];
    };
  }

  onSeaClick(arg) {
    if (!arg) return this.seaClickHandler;
    else this.seaClickHandler = arg;
    return this;
  }

  onCountryClick(arg) {
    if (!arg) return this.countryClickHandler;
    else this.countryClickHandler = arg;
    return this;
  }

  onCountryMouseOver(arg) {
    if (!arg) return this.countryMouseOverHandler;
    else this.countryMouseOverHandler = arg;
    return this;
  }

  onZoneMouseOut(arg) {
    if (!arg) return this.zoneMouseOutHandler;
    else this.zoneMouseOutHandler = arg;
    return this;
  }

  onZoneMouseMove(arg) {
    if (!arg) return this.zoneMouseMoveHandler;
    else this.zoneMouseMoveHandler = arg;
    return this;
  }

  onMouseMove(arg) {
    if (!arg) return this.mouseMoveHandler;
    else this.mouseMoveHandler = arg;
    return this;
  }

  onDragStart(arg) {
    this.dragStartHandlers.push(arg);
    return this;
  }

  onDrag(arg) {
    this.dragHandlers.push(arg);
    return this;
  }

  onDragEnd(arg) {
    this.dragEndHandlers.push(arg);
    return this;
  }

  onMapLoaded(arg) {
    this.mapLoadedHandlers.push(arg);
    return this;
  }

  setData(data) {
    this.data = data;
    this.clickableZoneGeometries = [];
    this.nonClickableZoneGeometries = [];

    Object.keys(data).forEach((k) => {
      const { geometry } = data[k];
      // Remove empty geometries
      geometry.coordinates = geometry.coordinates.filter(d => d.length !== 0);
      const feature = {
        type: 'Feature',
        geometry,
        properties: {
          zoneId: k,
          co2intensity: data[k].co2intensity,
        },
      };
      if (data[k].isClickable === undefined || data[k].isClickable === true) {
        this.clickableZoneGeometries.push(feature);
      } else {
        this.nonClickableZoneGeometries.push(feature);
      }
    });

    this.paintData();
    return this;
  }

  setCenter(center) {
    this.center = center;
    this.map.panTo(center);
    return this;
  }

  setZoom(zoom) {
    this.zoom = zoom;
    this.map.zoomTo(zoom);
    return this;
  }

  setScrollZoom(arg) {
    if (arg === true) {
      this.map.scrollZoom.enable();
    } else {
      this.map.scrollZoom.disable();
    }
    return this;
  }

  setDoubleClickZoom(arg) {
    if (arg === true) {
      this.map.doubleClickZoom.enable();
    } else {
      this.map.doubleClickZoom.disable();
    }
    return this;
  }
}
