import mapboxgl from 'mapbox-gl';

class Map {
  _setupMapColor() {
    if (this.map.isStyleLoaded()) {
      // TODO: Duplicated code
      const stops = this.co2color.range()
        .map((d, i) => [this.co2color.domain()[i], d]);
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
      // Create source
      this.map.addSource('world', {
        type: 'geojson',
        data,
      });
      // Create layers
      const stops = this.co2color.range()
        .map((d, i) => [this.co2color.domain()[i], d]);
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
        source: 'world',
        layout: {},
        paint: {
          'fill-color': 'white',
          'fill-opacity': 0.5,
        },
        filter: ['==', 'zoneId', ''],
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
      dragRotate: false,
      style: {
        version: 8,
        // transition: { duration: 500 },
        sources: {},
        layers: [],
        zoom: 3,
        center: this.center || [0, 50],
      },
    });

    this.map.on('load', () => {
      // Here we need to set all styles
      this.paintData();
      this._setupMapColor();
      this.mapLoadedHandlers.forEach(h => h(this));
    });

    // setInterval(() => console.log(this.map.loaded()), 500);
    this.map.on('dataloading', (e) => console.log('dataloading', e));
    this.map.on('styledataloading', () => console.log('styledataloading'));
    this.map.on('sourcedataloading', () => console.log('sourcedataloading'));

    // Add zoom and rotation controls to the map.
    this.map.addControl(new mapboxgl.NavigationControl());

    this.dragStartHandlers = [];
    this.dragHandlers = [];
    this.dragEndHandlers = [];
    this.mapLoadedHandlers = [];

    this.map.on('mouseenter', 'zones-fill', (e) => {
      this.map.getCanvas().style.cursor = 'pointer';
      if (this.countryMouseOverHandler) {
        const i = e.features[0].id;
        this.countryMouseOverHandler.call(this, this.data[i], i);
      }
    });
    let prevId;
    this.map.on('mousemove', 'zones-fill', (e) => {
      if (prevId !== e.features[0].properties.zoneId) {
        prevId = e.features[0].properties.zoneId;
        // ** TRY: setData() with just the poly instead
        this.map.setFilter(
          'zones-hover',
          ['==', 'zoneId', e.features[0].properties.zoneId],
        );
      }
      if (this.countryMouseMoveHandler) {
        const i = e.features[0].id;
        this.countryMouseMoveHandler.call(this, this.data[i], i, e.point.x, e.point.y);
      }
    });
    this.map.on('mouseleave', 'zones-fill', () => {
      this.map.getCanvas().style.cursor = '';
      this.map.setFilter('zones-hover', ['==', 'zoneId', '']);
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

    /* Adding the exchange layer 

    - inside #zones .mapboxgl-canvas-container (at the end)
    - exchange layer should be part of this?
    - create an arrow component

    */

    // *** PAN/ZOOM ***
    let dragInitialTransform;
    let dragStartTransform;
    let isDragging = false;

    const onPanZoom = (e) => {
      const transform = {
        x: e.target.transform.x,
        y: e.target.transform.y,
        k: e.target.transform.scale,
      };
      this.dragHandlers.forEach(h => h.call(this, transform));
    };

    let zoomEndTimeout;

    const onPanZoomStart = (e) => {
      // For some reason, MapBox gives us many start events inside a single zoom.
      // They are removed here:
      if (isDragging) { return; }
      isDragging = true;
      if (zoomEndTimeout) {
        clearTimeout(zoomEndTimeout);
        zoomEndTimeout = undefined;
      }
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
    };

    const onPanZoomEnd = () => {
      // Note that zoomend() methods are slow because they recalc layer.
      // Therefore, we debounce them.
      // TODO: Is this the right place to debounce?

      zoomEndTimeout = setTimeout(() => {
        this.dragEndHandlers.forEach(h => h.call(this));

        dragStartTransform = undefined;
        zoomEndTimeout = undefined;
      }, 500);

      isDragging = false;
    };

    this.map.on('drag', onPanZoom);
    this.map.on('zoom', onPanZoom);
    this.map.on('dragstart', onPanZoomStart);
    this.map.on('zoomstart', onPanZoomStart);
    this.map.on('dragend', onPanZoomEnd);
    this.map.on('zoomend', onPanZoomEnd);

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
