const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-scale'),
);

class ExchangeLayer {
  constructor(selectorId, map) {
    this.exchangeAnimationDurationScale = d3.scaleLinear()
      .domain([500, 5000])
      .range([1.5, 0])
      .clamp(true);

    this.rootNode = document.getElementById(selectorId);
    this.root = d3.select(this.rootNode);

    /* This is the transform applied to the whole layer */
    this.transform = { x: 0, y: 0, k: 1 };
    /* This is the transform applied at last render */
    this.initialTransform = undefined;
    /* This is the *map* transform applied at last render */
    this.initialMapTransform = undefined;

    this.projection = (lonlat) => {
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
        // Disable animations
        this.root.selectAll('.exchange-arrow img.highlight')
          .style('animation-play-state', 'paused');
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
        this.rootNode.style.transform =
          `translate(${this.transform.x}px,${this.transform.y}px) scale(${this.transform.k})`;
      })
      .onDragEnd(() => {
        // re-render to hide out-of-screen arrows
        this.render();
        // re-enable animations
        this.root.selectAll('.exchange-arrow img.highlight')
          .style('animation-play-state', null);
      });

    window.addEventListener('resize', () => this.render());
  }

  render() {
    if (!this.data) { return; }
    // Save initial transform
    this.initialTransform = Object.assign({}, this.transform);
    this.initialMapTransform = null;

    // Apply current transform (in case it wasn't applied before)
    this.rootNode.style.transform =
      `translate(${this.transform.x}px,${this.transform.y}px) scale(${this.transform.k})`;

    this.containerWidth = parseInt(this.rootNode.parentNode.getBoundingClientRect().width, 10);
    this.containerHeight = parseInt(this.rootNode.parentNode.getBoundingClientRect().height, 10);

    const exchangeArrows = this.root
      .selectAll('.exchange-arrow')
      .data(this.data, d => d.sortedCountryCodes);
    exchangeArrows.exit().remove();

    // This object refers to arrows created
    // Add all static properties
    const newArrows = exchangeArrows.enter()
      .append('div') // Add a group so we can animate separately
      .attr('class', 'exchange-arrow');
    const {
      exchangeMouseOverHandler,
      exchangeMouseOutHandler,
      exchangeMouseMoveHandler,
    } = this;
    newArrows
      .attr('width', 49)
      .attr('height', 81)
      .on('mouseover', function (d, i) { exchangeMouseOverHandler.call(this, d, i); })
      .on('mouseout', function (d, i) { exchangeMouseOutHandler.call(this, d, i); })
      .on('mousemove', function (d, i) { exchangeMouseMoveHandler.call(this, d, i); })
      .on('click', function (d, i) { exchangeClickHandler.call(this, d, i); });
    newArrows.append('img')
      .attr('class', 'base');
    newArrows.append('img')
      .attr('class', 'highlight')
      .attr('src', 'images/arrow-highlights/50.png');

    const arrowCarbonIntensitySliceSize = 80; // New arrow color at every X rise in co2
    const maxCarbonIntensity = 800; // we only have arrows up to a certain point

    // `merged` represents updates of all elements (both added and existing)
    const merged = newArrows.merge(exchangeArrows)
      .style('display', (d) => {
        const arrowCenter = this.projection(d.lonlat);
        // Compute position relative to container
        const relTransform = {
          x: (arrowCenter[0] * this.transform.k) + this.transform.x,
          y: (arrowCenter[0] * this.transform.k) + this.transform.x,
        };
        const isOffscreen =
          (relTransform.x < 0 || relTransform.x > this.containerWidth) &&
          (relTransform.y < 0 || relTransform.y > this.containerHeight);
        const hasLowFlow = (d.netFlow || 0) === 0;
        return (hasLowFlow || isOffscreen) ? 'none' : '';
      })
      .style('transform', (d) => {
        const center = this.projection(d.lonlat);
        const rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
        return `translate(${center[0]}px,${center[1]}px) rotate(${rotation}deg) scale(0.2)`;
      });
    merged.select('img.highlight')
      .style('animation-duration', d =>
        this.exchangeAnimationDurationScale(Math.abs(d.netFlow || 0)) + 's');
    merged.select('img.base')
      .attr('src', (d) => {
        let intensity = Math.min(
          maxCarbonIntensity,
          Math.floor(d.co2intensity - d.co2intensity % arrowCarbonIntensitySliceSize));
        if (d.co2intensity == null || Number.isNaN(intensity)) {
          intensity = 'nan';
        }
        return `images/arrow-${intensity}-outline.png`;
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

  setData(arg) {
    this.data = arg;
    return this;
  }
}

module.exports = ExchangeLayer;
