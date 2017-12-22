var d3 = require('d3');
import mapboxgl from 'mapbox-gl';

function _setupMapColor() {
  if (this._map.isStyleLoaded()) {
    // TODO: Duplicated code
    let that = this
    let stops = this._co2color.range()
      .map((d, i) => [that._co2color.domain()[i], d])
    this._map.setPaintProperty('zones-fill', 'fill-color', {
      default: 'gray',
      property: 'co2intensity',
      stops: stops,
    });
  }
}

function _setData() {
  if (!this._data) { return }
  let source = this._map.getSource('world')
  let data = {
    type: 'FeatureCollection',
    features: this._geometries
  }
  if (source) {
    source.setData(data)
  } else if (this._map.isStyleLoaded()) {
    // Create source
    this._map.addSource('world', {
      type: 'geojson',
      data: data
    })
    // Create layers
    let that = this
    let stops = this._co2color.range()
      .map((d, i) => [that._co2color.domain()[i], d])
    this._map.addLayer({
      id: 'zones-fill',
      type: 'fill',
      source: 'world',
      layout: {},
      paint: {
        // 'fill-color': 'gray', // ** TODO: Duplicated code
        'fill-color': {
          default: 'gray',
          property: 'co2intensity',
          stops: stops,
        }
      }
    })
    this._map.addLayer({
      id: 'zones-hover',
      type: 'fill',
      source: 'world',
      layout: {},
      paint: {
        'fill-color': 'white',
        'fill-opacity': 0.5,
      },
      filter: ['==', 'zoneId', '']
    })
    // Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer
    this._map.addLayer({
      id: 'zones-line',
      type: 'line',
      source: 'world',
      layout: {},
      paint: {
        'line-color': '#555555',
        'line-width': this.STROKE_WIDTH,
      }
    })
  }
}

function CountryMap(selectorId, wind, windCanvasSelector, solar, solarCanvasSelector) {
  let that = this;

  this.STROKE_WIDTH = 0.3;

  this.selectedCountry = undefined;

  this._center = undefined;
  this.startScale = 400;

  this.windCanvas = d3.select(windCanvasSelector);
  this.solarCanvas = d3.select(solarCanvasSelector);

  this._map = new mapboxgl.Map({
    container: selectorId, // selector id
    style: {
      version: 8,
      // transition: { duration: 500 },
      sources: {
        video: {
          type: 'video',
          urls: ['http://localhost:8000/twitter.mp4'],
          coordinates: [
            [-20, 20],
            [20, 20],
            [20, -20],
            [-20, -20],
          ],
        },
      },
      layers: [
        {
          id: 'video',
          type: 'raster',
          source: 'video',
        },
      ],
      zoom: 3,
      center: [0, 50],
    },
  });

  this._map.on('load', () => {
    // Here we need to set all styles
    _setData.call(that);
    _setupMapColor.call(that);
  });

  // Add zoom and rotation controls to the map.
  this._map.addControl(new mapboxgl.NavigationControl());

  this._map.on('mouseenter', 'zones-fill', e => {
    that._map.getCanvas().style.cursor = 'pointer'
    if (that.countryMouseOverHandler) {
      let i = e.features[0].id
      that.countryMouseOverHandler.call(this, that._data[i], i)
    }
  })
  let prevId = undefined
  this._map.on('mousemove', 'zones-fill', e => {
    if (prevId != e.features[0].properties.zoneId) {
      prevId = e.features[0].properties.zoneId
      that._map.setFilter('zones-hover',
        ['==', 'zoneId', e.features[0].properties.zoneId])
    }
    if (that.countryMouseMoveHandler) {
      let i = e.features[0].id
      that.countryMouseMoveHandler.call(this, that._data[i], i, e.point.x, e.point.y)
    }
  })
  this._map.on('mouseleave', 'zones-fill', e => {
    that._map.getCanvas().style.cursor = ''
    that._map.setFilter('zones-hover', ['==', 'zoneId', ''])
    if (that.countryMouseOutHandler) {
      that.countryMouseOutHandler.call(this)
    }
  })
  this._map.on('click', 'zones-fill', e => {
    if (that.countryClickHandler) {
      let i = e.features[0].id
      that.countryClickHandler.call(this, that._data[i], i)
    }
  })

  let arrowsLayer = d3.select('.arrows-layer')
  function onBoundsChanged(e) {
    console.log(e)
    let transform = {
      x: 0,//e.target.transform,
      y: 0,
      k: e.target.transform.scale
    }
    console.log(transform.k)
    arrowsLayer.style('transform',
      'translate(' + transform.x + 'px,' + transform.y + 'px) scale(' + transform.k + ')'
    );
  }
  // this._map.on('drag', onBoundsChanged);
  // this._map.on('zoom', onBoundsChanged);

  var dragStartTransform;

  // TODO: DO THE SAME ON ZOOM


  this._map.on('drag', e => {

  });
  this._map.on('dragstart', e => {
    if (that.zoomEndTimeout) {
      clearTimeout(that.zoomEndTimeout);
      that.zoomEndTimeout = undefined;
    }
    if (!dragStartTransform) {
      // Zoom start
      // dragStartTransform = d3.event.transform;
      wind.pause(true);
      // d3.select(this).style('cursor', 'move');
    }

    return;

    var transform = d3.event.transform;

    // Scale the svg g elements in order to keep control over stroke width
    // See https://github.com/tmrowco/electricitymap/issues/471
    that.land.attr('transform', transform);
    // that.graticule.attr('transform', transform);

    // If we don't want to scale the layer in order to keep the arrow size constant,
    // we will need to translate every arrow element by it's original dX multiplied by transform.k
    // Apply CSS transforms
    that.arrowsLayer.style('transform',
        'translate(' + transform.x + 'px,' + transform.y + 'px) scale(' + transform.k + ')'
    );

    var incrementalScale = transform.k / dragStartTransform.k;
    [that.windCanvas, that.solarCanvas].forEach(function(e) {
        e.style('transform',
            'translate(' +
            (transform.x - dragStartTransform.x * incrementalScale) + 'px,' +
            (transform.y - dragStartTransform.y * incrementalScale) + 'px)' +
            'scale(' + incrementalScale + ')'
        );
    });
  })

  this._map.on('dragend', e => {
    // Note that zoomend() methods are slow because they recalc layer.
    // Therefore, we debounce them.

    var zoomEl = this;
    // var d3Event = d3.event;

    that.zoomEndTimeout = setTimeout(function() {
        that.exchangeLayer().render();
        // d3.select(zoomEl).style('cursor', undefined);

        // Here we need to update the (absolute) projection in order to be used by other systems
        // that would like to overlay the map
        /*var projection = that._absProjection;
        if (!projection) { return; }
        var transform = d3Event.transform;
        var scale = that.startScale * transform.k;
        projection
            .scale(scale)
            .translate([
                scale * Math.PI + transform.x,
                scale * Math.PI + transform.y]);*/

        // Notify. This is where we would need a Reactive / Pub-Sub system instead.
        wind.zoomend();
        solar.zoomend();
        that.windCanvas.style('transform', undefined);
        that.solarCanvas.style('transform', undefined);
        wind.pause(false);

        that.dragEndHandler.call(zoomEl);

        dragStartTransform = undefined;
        that.zoomEndTimeout = undefined;
    }, 500)
  })

  return;

  this.root = d3.select(selector)
      // Position needs to be absolute in order not to force the
      // container not to grow to the map's size
      .style('position', 'absolute')
      .style('transform-origin', '0px 0px')
      .style('transform', 'translate(0px,0px) scale(1)'); // Safari bug causes map to appear on top of other things unless translated
  // Add SVG layer
  this.svg = this.root.append('svg')
      .attr('class', 'map-layer')
      .on('click', function (d, i) {
          if (that.selectedCountry !== undefined) {
              that.selectedCountry
                  .style('stroke', undefined)
                  .style('stroke-width', that.STROKE_WIDTH);
          }
          if (that.seaClickHandler)
              that.seaClickHandler.call(this, d, i);
      });
  // Add SVG elements
  // this.graticule = this.svg.append('g').append('path')
  //     .attr('class', 'graticule');
  this.land = this.svg.append('g')
      .attr('class', 'land');
  // Add other layers
  this.arrowsLayer = this.root.append('div')
      .attr('class', 'arrows-layer map-layer')
      .style('transform-origin', '0px 0px');

  this.zoom = d3.zoom().on('zoom', function() {
      
  })
  .on('end', function() {
      
  });

  d3.select(this.root.node().parentNode).call(this.zoom);
}

CountryMap.prototype.render = function() {

    const that = this

    return

    // Determine scale (i.e. zoom) based on the size
    this.containerWidth = this.root.node().parentNode.getBoundingClientRect().width;
    this.containerHeight = this.root.node().parentNode.getBoundingClientRect().height;

    // Nothing to render
    if (!this.containerHeight || !this.containerWidth)
        return this;

    // The projection shouldn't change
    if (!this._projection || !this._absProjection) {
        var scale = this.startScale;
        this._projection = d3.geoMercator()
            .rotate([0,0])
            .scale(scale)
            .translate([scale * Math.PI, scale * Math.PI]); // Warning, default translation is [480, 250]
        // There's no clone function unfortunately
        this._absProjection = d3.geoMercator()
            .rotate([0,0])
            .scale(scale)
            .translate([scale * Math.PI, scale * Math.PI]); // Warning, default translation is [480, 250]
    }

    // taken from http://bl.ocks.org/patricksurry/6621971
    // find the top left and bottom right of current projection
    function mercatorBounds(projection, maxlat) {
        var yaw = projection.rotate()[0],
            xymax = projection([-yaw+180-1e-6,-maxlat]),
            xymin = projection([-yaw-180+1e-6, maxlat]);
        
        return [xymin,xymax];
    }

    var maxlat = 83; // clip northern and southern poles (infinite in mercator)
    var b = mercatorBounds(this._projection, maxlat);
    this.mapWidth = b[1][0] - b[0][0];
    this.mapHeight = b[1][1] - b[0][1];

    if (this.mapHeight == 0 || this.mapWidth == 0) {
        throw Error('Invalid map dimensions');
    }

    // Width and height should nevertheless never be smaller than the container
    this.mapWidth  = Math.max(this.mapWidth,  this.containerWidth);
    this.mapHeight = Math.max(this.mapHeight, this.containerHeight);

    this.zoom
        .scaleExtent([0.5, 6])
        .translateExtent([[0, 0], [this.mapWidth, this.mapHeight]]);

    this.root
        .style('height', this.mapHeight + 'px')
        .style('width', this.mapWidth + 'px');
    this.svg
        .style('height', this.mapHeight + 'px')
        .style('width', this.mapWidth + 'px');

    this.path = d3.geoPath()
        .projection(this._projection);
        
    // var graticuleData = d3.geoGraticule()
    //     .step([5, 5]);
        
    // this.graticule
    //     .datum(graticuleData)
    //     .attr('d', this.path);

    if (this._data) {
        var selector = this.land.selectAll('.country')
            .data(this._data, function(d) { return d.countryCode; });
        var pathEnter = selector.enter()
            .append('path')
                .attr('class', 'country')
                .attr('stroke-width', that.STROKE_WIDTH)
                .attr('d', this.path) // path is only assigned on create
        if (!(/iPad|iPhone|iPod/.test(navigator.userAgent))) {
            // Only set click events to every but Apple mobile devices
            // to avoid the Safari double tap issue
            pathEnter = pathEnter
                .on('mouseover', function (d, i) {
                    if (that.countryMouseOverHandler)
                        return that.countryMouseOverHandler.call(this, d, i);
                })
                .on('mouseout', function (d, i) {
                    if (that.countryMouseOutHandler)
                        return that.countryMouseOutHandler.call(this, d, i);
                })
                .on('mousemove', function (d, i) {
                    if (that.countryMouseMoveHandler)
                        return that.countryMouseMoveHandler.call(this, d, i);
                })
        }
        pathEnter.on('click',
            // Test for Googlebot crawler in order to pass
            // mobile-friendly test
            // Else, Googlebot complains that elements are not wide enough
            // to be clicked.
            navigator.userAgent.indexOf('Googlebot') != -1 ?
                undefined :
                function (d, i) {
                    d3.event.stopPropagation(); // To avoid call click on sea
                    if (that.selectedCountry !== undefined) {
                        that.selectedCountry
                            .style('stroke', that.STROKE_COLOR)
                            .style('stroke-width', that.STROKE_WIDTH);
                    }
                    that.selectedCountry = d3.select(this);
                    // that.selectedCountry
                    //     .style('stroke', 'darkred')
                    //     .style('stroke-width', 1.5);
                    return that.countryClickHandler.call(this, d, i);
                })
        .merge(selector)
            .transition()
            .duration(2000)
            .attr('fill', this.getCo2Color);
    }

    return this;
}

CountryMap.prototype.co2color = function(arg) {
  if (!arg) return this._co2color;
  else {
    this._co2color = arg
    _setupMapColor.call(this)
  }
  return this;
};

CountryMap.prototype.exchangeLayer = function(arg) {
    if (!arg) return this._exchangeLayer;
    else this._exchangeLayer = arg;
    return this;
};

CountryMap.prototype.projection = function() {
  // Read-only property
  const that = this;
  return (lonlat) => {
    const p = this._map.project(lonlat);
    return [p.x, p.y];
  }
};

CountryMap.prototype.unprojection = function() {
   // Read-only property
  const that = this;
  return (xy) => {
    const p = this._map.unproject(xy);
    return [p.lng, p.lat];
  }
};

CountryMap.prototype.onSeaClick = function(arg) {
    if (!arg) return this.seaClickHandler;
    else this.seaClickHandler = arg;
    return this;
};

CountryMap.prototype.onCountryClick = function(arg) {
    if (!arg) return this.countryClickHandler;
    else this.countryClickHandler = arg;
    return this;
};

CountryMap.prototype.onCountryMouseOver = function(arg) {
    if (!arg) return this.countryMouseOverHandler;
    else this.countryMouseOverHandler = arg;
    return this;
};

CountryMap.prototype.onCountryMouseMove = function(arg) {
    if (!arg) return this.countryMouseMoveHandler;
    else this.countryMouseMoveHandler = arg;
    return this;
};

CountryMap.prototype.onCountryMouseOut = function(arg) {
    if (!arg) return this.countryMouseOutHandler;
    else this.countryMouseOutHandler = arg;
    return this;
};

CountryMap.prototype.onDragEnd = function(arg) {
    if (!arg) return this.dragEndHandler;
    else this.dragEndHandler = arg;
    return this;
};

CountryMap.prototype.data = function(data) {
  if (!data) {
    return this._data;
  } else {
    this._data = data;
    this._geometries = []

    let that = this

    Object.keys(data).forEach((k, i) => {
      let geometry = data[k]
      // Remove empty geometries
      geometry.coordinates = geometry.coordinates.filter(d => d.length != 0)

      that._geometries.push({
          'id': k,
          'type': 'Feature',
          'geometry': geometry,
          'properties': {
              'zoneId': k,
              'co2intensity': data[k].co2intensity
          }
      })
    })

    _setData.call(this)
    
  }
  return this;
};

CountryMap.prototype.center = function(center) {
    if (!center) {
        return this._center;
    } else if (this._center) {
        // Only allow setting the center once in order to avoid
        // quirky UX due to sporadic re-centering
        console.warn('Center has already been set.');
        return this;
    } else if (!this._projection) {
        console.warn('Can\'t change center when projection is not already set.');
        return this;
    } else {
        var p = this._projection(center);
        var dx = -1 * p[0] + 0.5 * this.containerWidth;
        var dy = -1 * p[1] + 0.5 * this.containerHeight;

        var scale = this.startScale;

        // Clip
        if (dx > 0) dx = 0;
        if (dx < this.containerWidth - this.mapWidth) dx = this.containerWidth - this.mapWidth;
        if (dy > 0) dy = 0;
        if (dy < this.containerHeight - this.mapHeight) dy = this.containerHeight - this.mapHeight;

        this.zoom
            .translateBy(d3.select(this.root.node().parentNode), // WARNING, this is accumulative.
                dx, dy);
        this._center = center;

        this._map.setCenter(center)

        // Update absolute projection
        this._absProjection
            .translate([
                scale * Math.PI + dx,
                scale * Math.PI + dy,
            ]);
    }
    return this;
}

module.exports = CountryMap;
