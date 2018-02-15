import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

export default class Map {
  _setupMapColor() {
    if (this.map.isStyleLoaded() && this.map.getLayer('clickable-zones-fill') && this.co2color) {
      // TODO: Duplicated code
      const co2Range = [0, 200, 400, 600, 800, 1000];
      const stops = co2Range.map(d => [d, this.co2color(d)]);
      this.map.setPaintProperty('clickable-zones-fill', 'fill-color', {
        default: 'gray',
        property: 'co2intensity',
        stops,
      });
    }
  }

  paintData() {
    if (!this.data) { return; }
    const clickableSource = this.map.getSource('clickable-world');
    const nonClickableSource = this.map.getSource('non-clickable-world');
    const oceanSource = this.map.getSource('ocean-world');
    const clickableData = {
      type: 'FeatureCollection',
      features: this.clickableZoneGeometries,
    };
    const nonClickableData = {
      type: 'FeatureCollection',
      features: this.nonClickableZoneGeometries,
    };
    const oceanData = this.oceanData;
    if (clickableSource && nonClickableSource && oceanSource) {
      clickableSource.setData(clickableData);
      nonClickableSource.setData(nonClickableData);
      oceanSource.setOceanData(oceanData);
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
        data: {
          type: 'FeatureCollection',
          features: [],
        },
      });
      this.map.addSource('ocean-world', {
        type: 'geojson',
        data: oceanData
      });
      const paint = {
        'fill-color': this.clickableFill,
      };
      if (this.co2color) {
        const co2Range = [0, 200, 400, 600, 800, 1000];
        const stops = co2Range.map(d => [d, this.co2color(d)]);
        paint['fill-color'] = {
          stops,
          property: 'co2intensity',
          default: this.clickableFill,
        };
      }
      // Create layers
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
        paint: { 'fill-color': this.nonClickableFill },
      });
      this.map.addLayer({
        id: 'ocean-fill',
        type: 'fill',
        source: 'ocean-world',
        layout: {},
        paint: {
          'fill-color': 'blue',
          'fill-opacity': 0.3,
        }
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
      });
      // Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer
      this.map.addLayer({
        id: 'zones-line',
        type: 'line',
        source: 'clickable-world',
        layout: {},
        paint: {
          'line-color': this.strokeColor,
          'line-width': this.strokeWidth,
        },
      });
    }
  }

  constructor(selectorId, argConfig) {
    const config = argConfig || {};

    this.strokeWidth = config.strokeWidth || 0.3;
    this.strokeColor = config.strokeColor || '#555555';
    this.clickableFill = config.clickableFill || 'gray';
    this.nonClickableFill = config.nonClickableFill || 'gray';
    this.userIsUsingTouch = false;

    this.center = undefined;

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
        zoom: config.zoom || 3,
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
    const node = document.getElementById(selectorId);
    let boundingClientRect = node.getBoundingClientRect();
    window.addEventListener('resize', () => {
      boundingClientRect = node.getBoundingClientRect();
    });
    this.map.on('mousemove', 'clickable-zones-fill', (e) => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      if (prevId !== e.features[0].properties.zoneId) {
        prevId = e.features[0].properties.zoneId;
        const hoverSource = this.map.getSource('hover');
        if (hoverSource) {
          hoverSource.setData(e.features[0]);
        }
      }
      if (this.countryMouseMoveHandler) {
        const i = e.features[0].properties.zoneId;
        const rect = boundingClientRect;
        const p = this.map.unproject([e.point.x, e.point.y]);
        this.countryMouseMoveHandler.call(
          this,
          this.data[i],
          i,
          rect.left + e.point.x,
          rect.top + e.point.y,
          [p.lng, p.lat],
        );
      }
    });
    this.map.on('mousemove', 'ocean-fill', (e) => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      if (this.oceanMouseMoveHandler) {
        const p = this.map.unproject([e.point.x, e.point.y]);
        this.oceanMouseMoveHandler.call(
          this,
          [p.lng, p.lat],
        );
      }
    });

    this.map.on('mouseleave', 'clickable-zones-fill', () => {
      // Disable for touch devices
      if (this.userIsUsingTouch) { return; }
      this.map.getCanvas().style.cursor = '';
      this.map.getSource('hover').setData({
        type: 'FeatureCollection',
        features: [],
      });
      prevId = null;
      if (this.countryMouseOutHandler) {
        this.countryMouseOutHandler.call(this);
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

  setCo2color(arg) {
    this.co2color = arg;
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

  onCountryMouseMove(arg) {
    if (!arg) return this.countryMouseMoveHandler;
    else this.countryMouseMoveHandler = arg;
    return this;
  }

  onOceanMouseMove(arg) {
    if (!arg) return this.oceanMouseMoveHandler;
    else this.oceanMouseMoveHandler = arg;
    return this;
  }

  onCountryMouseOut(arg) {
    if (!arg) return this.countryMouseOutHandler;
    else this.countryMouseOutHandler = arg;
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
      const geometry = data[k].geometry;
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

  setOceanData(data) {
    this.oceanData = data;
    this.paintData();
    return this;
  }

  setCenter(center) {
    this.center = center;
    this.map.panTo(center);
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
