var d3 = require('d3');

class ExchangeLayer {
  constructor(selector, arrowsSelector, map) {
    this.exchangeAnimationDurationScale = d3.scaleLinear()
        .domain([500, 5000])
        .range([1.5, 0])
        .clamp(true);

    this.root = d3.select(arrowsSelector);
    const rootNode = this.root.node();

    /* This is the transform applied to the whole layer */
    this.transform = { x: 0, y: 0, k: 1 };
    /* This is the transform applied at last render */
    this.initialTransform;
    /* This is the *map* transform applied at last render */
    this.initialMapTransform;

    this._projection = (lonlat) => {
      /*
      `map.projection()` is relative to viewport
      Because the layer might already have a transform applied when dragged,
      we need to compensate.
      */
      const p = map.projection()(lonlat);
      return [
          (p[0] - this.transform.x) / this.transform.k,
          (p[1] - this.transform.y) / this.transform.k,
      ];
    };
    
    map
      .onDragStart((transform) => {
        if (!this.initialMapTransform) {
          this.initialMapTransform = transform;
        }
      })
      .onDrag((transform) => {
        if (!this.initialTransform) { return; }
        // `relTransform` is the transform of the map
        // since the last render
        const relScale = transform.k / this.initialMapTransform.k;
        const relTransform = {
          x: transform.x - (this.initialMapTransform.x * relScale),
          y: transform.y - (this.initialMapTransform.y * relScale),
          k: relScale,
        };

        // This layer already has some transformation applied.
        // We only want to change it by the "delta".
        // We therefore need to "sum" the map transform since drag
        // with our current already applied transform
        this.transform = {
          x: this.initialTransform.x - relTransform.x + (1 - relTransform.k) * (0.5 * this.containerWidth - this.initialTransform.x),
          y: this.initialTransform.y - relTransform.y + (1 - relTransform.k) * (0.5 * this.containerHeight - this.initialTransform.y),
          k: this.initialTransform.k * relTransform.k, // arrow size scales correctly
        };
        rootNode.style.transform =
          `translate(${this.transform.x}px,${this.transform.y}px) scale(${this.transform.k})`;
      });

    window.addEventListener('resize', () => this.render());
  }

  render() {
    if (!this._data) { return; }
    // Abort if projection has not been set
    if (!this._projection) { return; }
    console.log('Exchange render')
    this.initialTransform = Object.assign({}, this.transform);
    this.initialMapTransform = null;
    console.log('Saving transform', this.transform)
    console.warn('TODO: Make sure that we only draw visible arrows')

    // Apply current transform (in case it wasn't applied before)
    this.root.node().style.transform =
      `translate(${this.transform.x}px,${this.transform.y}px) scale(${this.transform.k})`;

    const node = this.root.node();
    this.containerWidth = parseInt(node.parentNode.getBoundingClientRect().width);
    this.containerHeight = parseInt(node.parentNode.getBoundingClientRect().height);

    var exchangeArrows = this.root
      .selectAll('.exchange-arrow')
      .data(this._data, d => d);
    exchangeArrows.exit().remove();

    // This object refers to arrows created
    // Add all static properties
    var newArrows = exchangeArrows.enter()
      .append('div') // Add a group so we can animate separately
      .attr('class', 'exchange-arrow');
    newArrows
      .attr('width', 49)
      .attr('height', 81)
      .on('mouseover', (d, i) => {
        return this.exchangeMouseOverHandler.call(this, d, i);
      })
      .on('mouseout', (d, i) => {
        return this.exchangeMouseOutHandler.call(this, d, i);
      })
      .on('mousemove', (d, i) => {
        return this.exchangeMouseMoveHandler.call(this, d, i);
      })
      .on('click', (d, i) => {
        return this.exchangeClickHandler.call(this, d, i);
      });
    newArrows.append('img')
      .attr('class', 'base')
    newArrows.append('img')
      .attr('class', 'highlight')
      .attr('src', 'images/arrow-highlights/50.png');
    
    var arrowCarbonIntensitySliceSize = 80; // New arrow color at every X rise in co2
    var maxCarbonIntensity = 800; // we only have arrows up to a certain point

    var layerTransform = (this.root.style('transform') || "matrix(1, 0, 0, 1, 0, 0)")
      .replace(/matrix\(|\)/g, '').split(/\s*,\s*/);

    const merged = newArrows.merge(exchangeArrows)
      .style('display', (d) => {
        var arrowCenter = this._projection(d.lonlat);
        var layerTranslateX = layerTransform[4];
        var mapScale = layerTransform[3];
        var centerX = (arrowCenter[0] * mapScale) - Math.abs(layerTranslateX);
        var isOffscreen = centerX < 0 || centerX > this.containerWidth;
        var hasLowFlow = (d.netFlow || 0) == 0;
        return (hasLowFlow || isOffscreen) ? 'none' : '';
      })
      .style('transform', (d) => {
        var center = this._projection(d.lonlat);
        var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
        return 'translateX(' + center[0] + 'px) translateY(' + center[1] + 'px) rotate(' + rotation + 'deg) scale(0.2)';
      });
    merged.select('img.highlight')
      .style('animation-duration', d =>
        this.exchangeAnimationDurationScale(Math.abs(d.netFlow || 0)) + 's');
    merged.select('img.base')
      .attr('src', (d) => {
        var intensity = Math.min(maxCarbonIntensity, Math.floor(d.co2intensity - d.co2intensity%arrowCarbonIntensitySliceSize));
        if (d.co2intensity == null || isNaN(intensity)) intensity = 'nan';
        return 'images/arrow-' + intensity + '-outline.png';
      });

    return this;
  }


  onExchangeMouseOver(arg) {
    if (!arg) return this.exchangeMouseOverHandler;
    else this.exchangeMouseOverHandler = arg;
    return this;
  }

  onExchangeMouseMove(arg) {
    if (!arg) return this.exchangeMouseMoveHandler;
    else this.exchangeMouseMoveHandler = arg;
    return this;
  }

  onExchangeMouseOut(arg) {
    if (!arg) return this.exchangeMouseOutHandler;
    else this.exchangeMouseOutHandler = arg;
    return this;
  }

  onExchangeClick(arg) {
    if (!arg) return this.exchangeClickHandler;
    else this.exchangeClickHandler = arg;
    return this;
  }

  co2color(arg) {
    if (!arg) return this._co2color;
    else this._co2color = arg;
    return this;
  }

  data(arg) {
    if (!arg) return this._data;
    else {
      this._data = arg;
    }
    return this;
  }
}

module.exports = ExchangeLayer;
