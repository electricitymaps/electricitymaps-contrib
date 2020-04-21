/* eslint-disable */
// TODO: remove once refactored

const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-scale'),
);

import {event as d3Event} from 'd3-selection';

const global = require('../../global').default;

class ExchangeLayer {
  constructor(selectorId) {
    this.exchangeAnimationDurationScale = d3.scaleLinear()
      .domain([500, 5000])
      .rangeRound([0, 2])
      .clamp(true);
    this.colorblindMode = false;
    this.rootNode = document.getElementById(selectorId);
    this.root = d3.select(this.rootNode);

    /* This is the transform applied to the whole layer */
    this.transform = { x: 0, y: 0, k: 1 };
    /* This is the transform applied at last render */
    this.initialTransform = undefined;
    /* This is the *map* transform applied at last render */
    this.initialMapTransform = undefined;

    /* Set arrow scale */
    this.arrowScale = 0.04 + (global.zoneMap.map.getZoom() - 1.5) * 0.1;

    this.projection = (lonlat) => {
      /*
      `map.projection()` is relative to viewport
      Because the layer might already have a transform applied when dragged,
      we need to compensate.
      */
      const p = global.zoneMap.projection()(lonlat);
      return [
        (p[0] - this.transform.x) / this.transform.k,
        (p[1] - this.transform.y) / this.transform.k,
      ];
    };

    global.zoneMap
      .onDragStart((transform) => {
        if (!this.initialMapTransform) {
          this.initialMapTransform = transform;
        }
        // Disable animations
        this.root.selectAll('.exchange-arrow img.highlight')
          .style('animation-play-state', 'paused');
        this.rootNode.style.display = 'none';
      })
      .onDrag((transform) => {
        if (!this.initialMapTransform || !this.initialTransform) { return; }
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
          `translateX(${this.transform.x}px) translateY(${this.transform.y}px) translateZ(0) scale(${this.transform.k})`;
      })
      .onDragEnd(() => {
        // re-render to hide out-of-screen arrows
        this.rootNode.style.display = 'inherit';
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
      `translateX(${this.transform.x}px) translateY(${this.transform.y}px) translateZ(0) scale(${this.transform.k})`;

    // Note: Depending on where the node is placed,
    // the immediate parent might not be the container
    this.containerWidth = parseInt(this.rootNode.parentNode.parentNode.getBoundingClientRect().width, 10);
    this.containerHeight = parseInt(this.rootNode.parentNode.parentNode.getBoundingClientRect().height, 10);

    const exchangeArrows = this.root
      .selectAll('.exchange-arrow')
      .data(this.data, d => d.sortedZoneKeys);
    exchangeArrows.exit().remove();

    // This object refers to arrows created
    // Add all static properties
    const newArrows = exchangeArrows.enter()
      .append('img')
      .attr('class', 'exchange-arrow')
      .attr('width', 49)
      .attr('height', 81)
      .style('image-rendering', 'crisp-edges');
    const {
      exchangeMouseOverHandler,
      exchangeMouseOutHandler,
      exchangeMouseMoveHandler,
      exchangeClickHandler,
    } = this;
    newArrows
      .on('mouseover', function (d, i) {
        d3Event.stopPropagation();
        if (exchangeMouseOverHandler) {
          exchangeMouseOverHandler.call(this, d, i);
        }
      })
      .on('mouseout', function (d, i) {
        d3Event.stopPropagation();
        if (exchangeMouseOutHandler) {
          exchangeMouseOutHandler.call(this, d, i);
        }
      })
      .on('mousemove', function (d, i) {
        d3Event.stopPropagation();
        if (exchangeMouseMoveHandler) {
          exchangeMouseMoveHandler.call(this, d, i);
        }
      })
      .on('click', function (d, i) {
        if (exchangeClickHandler) {
          exchangeClickHandler.call(this, d, i);
        }
      });

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
        const hasLowFlow = Math.abs(d.netFlow || 0) < 1;
        return (hasLowFlow || isOffscreen) ? 'none' : '';
      })
      .style('transform', (d) => {
        const center = this.projection(d.lonlat);
        const rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
        return `translateX(${center[0]}px) translateY(${center[1]}px) rotate(${rotation}deg) scale(${this.arrowScale}) translateZ(0)`;
      });
    merged
      .attr('src', (d) => {
        let intensity = Math.min(
          maxCarbonIntensity,
          Math.floor(d.co2intensity - d.co2intensity % arrowCarbonIntensitySliceSize));
        if (d.co2intensity == null || Number.isNaN(intensity)) {
          intensity = 'nan';
        }
        const prefix = this.colorblindMode ? 'colorblind-' : ''
        const duration = +this.exchangeAnimationDurationScale(Math.abs(d.netFlow || 0));
        return resolvePath(`images/${prefix}arrow-${intensity}-animated-${duration}.gif`);
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
    this.data = arg.filter(d => d.lonlat);
    return this;
  }

  setColorblindMode(arg) {
    this.colorblindMode = arg;
    return this;
  }
}

export default ExchangeLayer;
