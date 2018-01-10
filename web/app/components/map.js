import mapboxgl from 'mapbox-gl';

class Map {
  _setupMapColor() {
    if (this.map.isStyleLoaded()) {
      // TODO: Duplicated code
      const co2Range = [0, 200, 400, 600, 800, 1000];
      const stops = co2Range.map(d => [d, this.co2color(d)]);
      this.map.setPaintProperty('zones-fill', 'fill-color', {
        default: 'gray',
        property: 'co2intensity',
        stops,
      });
    }
  }

  paintData() {
    if (!this.data) { return; }
    const source = this.map.getSource('world');
    const data = {
      type: 'FeatureCollection',
      features: this.zoneGeometries,
    };
    if (source) {
      source.setData(data);
    } else if (this.map.isStyleLoaded()) {
      // Create sources
      this.map.addSource('world', {
        type: 'geojson',
        data,
      });
      this.map.addSource('hover', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [],
        },
      });
      // Create layers
      const co2Range = [0, 200, 400, 600, 800, 1000];
      const stops = co2Range.map(d => [d, this.co2color(d)]);
      this.map.addLayer({
        id: 'zones-fill',
        type: 'fill',
        source: 'world',
        layout: {},
        paint: {
          // 'fill-color': 'gray', // ** TODO: Duplicated code
          'fill-color': {
            default: 'gray',
            property: 'co2intensity',
            stops,
          },
        },
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
        source: 'world',
        layout: {},
        paint: {
          'line-color': '#555555',
          'line-width': this.STROKE_WIDTH,
        },
      });
    }
  }

  constructor(selectorId) {
    this.STROKE_WIDTH = 0.3;

    this.center = undefined;

    this.map = new mapboxgl.Map({
      container: selectorId, // selector id
      attributionControl: false,
      scrollZoom: true,
      style: {
        version: 8,
        sources: {},
        layers: [],
        zoom: 3,
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
        this.mapLoadedHandlers.forEach(h => h(this));
        clearInterval(loadingInterval);
      }
    }, 100);

    // Add zoom and rotation controls to the map.
    this.map.addControl(new mapboxgl.NavigationControl());

    this.dragStartHandlers = [];
    this.dragHandlers = [];
    this.dragEndHandlers = [];
    this.mapLoadedHandlers = [];

    this.map.on('mouseenter', 'zones-fill', (e) => {
      // Disable for touch devices
      if ('ontouchstart' in document.documentElement) { return; }
      this.map.getCanvas().style.cursor = 'pointer';
      if (this.countryMouseOverHandler) {
        const i = e.features[0].id;
        this.countryMouseOverHandler.call(this, this.data[i], i);
      }
    });

    let prevId;
    const node = document.getElementById(selectorId);
    let boundingClientRect = node.getBoundingClientRect();
    window.addEventListener('resize', () => {
      boundingClientRect = node.getBoundingClientRect();
    });
    this.map.on('mousemove', 'zones-fill', (e) => {
      // Disable for touch devices
      if ('ontouchstart' in document.documentElement) { return; }
      if (prevId !== e.features[0].properties.zoneId) {
        prevId = e.features[0].properties.zoneId;
        const hoverSource = this.map.getSource('hover');
        if (hoverSource) {
          hoverSource.setData(e.features[0]);
        }
      }
      if (this.countryMouseMoveHandler) {
        const i = e.features[0].id;
        const rect = boundingClientRect;
        this.countryMouseMoveHandler.call(
          this,
          this.data[i],
          i,
          rect.left + e.point.x,
          rect.top + e.point.y,
        );
      }
    });

    this.map.on('mouseleave', 'zones-fill', () => {
      // Disable for touch devices
      if ('ontouchstart' in document.documentElement) { return; }
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
        const i = features[0].id;
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
    this.zoneGeometries = [];

    Object.keys(data).forEach((k) => {
      const geometry = data[k];
      // Remove empty geometries
      geometry.coordinates = geometry.coordinates.filter(d => d.length !== 0);

      this.zoneGeometries.push({
        id: k,
        type: 'Feature',
        geometry,
        properties: {
          zoneId: k,
          co2intensity: data[k].co2intensity,
        },
      });
    });

    this.paintData();
    return this;
  }

  setCenter(center) {
    this.center = center;
    this.map.panTo(center);
    return this;
  }
}

module.exports = Map;
