var d3 = require('d3');

function ExchangeLayer(selector, arrowsSelector) {
    this.TRIANGLE_HEIGHT = 1.0;
    this.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT = 0.2;
    this.STROKE_CO2_THRESHOLD = 550;
    this.exchangeAnimationDurationScale = d3.scaleLinear()
        .domain([500, 5000])
        .rangeRound([0, 2])
        .clamp(true);

    this.root = d3.select(selector);
    this.exchangeArrowsContainer = d3.select(arrowsSelector);

    this.trianglePath = function() {
        var hh = this.TRIANGLE_HEIGHT / 2.0; // half-height
        var hb = this.TRIANGLE_HEIGHT; // half-base with base = 0.5 * height
        return 'M -' + hb + ' -' + hh + ' ' + 
        'L 0 ' + hh + ' ' + 
        'L ' + hb + ' -' + hh + ' Z ' +
        'M -' + hb + ' ' + hh + ' ' + 
        'L 0 ' + (3.0 * hh) + ' ' + 
        'L ' + hb + ' ' + hh + ' Z ' +
        'M -' + hb + ' -' + (3.0 * hh) + ' ' + 
        'L 0 -' + hh + ' ' + 
        'L ' + hb + ' -' + (3.0 * hh) + ' Z';
    };
}

ExchangeLayer.prototype.arrowScale = function(arg) {
    if (!arg) return this._arrowScale;
    else this._arrowScale = arg;
    return this;
};

ExchangeLayer.prototype.projection = function(arg) {
    if (!arg) return this._projection;
    else this._projection = arg;
    return this;
};

function appendGradient(element, triangleHeight) {
    return element.append('linearGradient')
        .attr('class', 'exchange-gradient')
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', 0).attr('y1', -2.0 * triangleHeight - 1)
        .attr('x2', 0).attr('y2', triangleHeight + 1);
}

ExchangeLayer.prototype.render = function() {
    if (!this._data) { return; }
    // Abort if projection has not been set
    if (!this._projection) { return; }
    var that = this;

    var exchangeArrows = this.exchangeArrowsContainer
        .selectAll('.exchange-arrow')
        .data(this._data, function(d) { return d; });
    exchangeArrows.exit().remove();

    // Calculate arrow scale
    // Note: the scaling should be based on the same metric as countryMap
    this.arrowScale(0.1);

    function updateArrows(selector) {
        var arrowCarbonIntensitySliceSize = 80; // New arrow color at every X rise in co2
        var maxCarbonIntensity = 800; // we only have arrows up to a certain point

        selector.style('display', function (d) {
            return (d.netFlow || 0) == 0 ? 'none' : '';
        })
        .style('transform', function (d) {
            var center = that.projection()(d.lonlat);
            var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
            return 'translateX(' + center[0] + 'px) translateY(' + center[1] + 'px) rotate(' + rotation + 'deg)';
        })
        .select('img')
        .attr('src', function (d) {
            var intensity = Math.min(maxCarbonIntensity, Math.floor(d.co2intensity - d.co2intensity%arrowCarbonIntensitySliceSize));
            if(isNaN(intensity)) intensity = 'nan';
            return 'images/arrow-'+intensity+'-animated-'+that.exchangeAnimationDurationScale(Math.abs(d.netFlow || 0))+'.gif';
        });
    }

    // This object refers to arrows created
    // Add all static properties
    var newArrows = exchangeArrows.enter()
        .append('div') // Add a group so we can animate separately
        .attr('class', 'exchange-arrow');
    newArrows.append('img')
        .attr('width', 49)
        .attr('height', 81)
        .style('transform', 'scale(' + this.arrowScale() + ')')
        .on('mouseover', function (d, i) {
            return that.exchangeMouseOverHandler.call(this, d, i);
        })
        .on('mouseout', function (d, i) {
            return that.exchangeMouseOutHandler.call(this, d, i);
        })
        .on('mousemove', function (d, i) {
            return that.exchangeMouseMoveHandler.call(this, d, i);
        })
        .on('click', function (d) { console.log(d); });

    // Because each key is unique, new elements will be added and old ones will be destroyed
    // This allows us to avoid re-rendering when the same element subsides between renders
    updateArrows(newArrows);

    // However, set the visibility
    var mapWidth = d3.select('#map-container').node().getBoundingClientRect().width;
    var layerTransform = d3.select('.arrows-layer').style('transform').replace(/matrix\(|\)/g, '').split(/\s*,\s*/);
    
    newArrows.merge(exchangeArrows)
        .style('display', function(d) {
            var arrowCenter = that.projection()(d.lonlat);
            var layerTranslateX = layerTransform[4];
            var mapScale = layerTransform[3];
            var centerX = (arrowCenter[0] * mapScale) - Math.abs(layerTranslateX);

            var isOffscreen = centerX < 0 || centerX > mapWidth;
            var hasLowFlow = (d.netFlow || 0) == 0;
            return (hasLowFlow || isOffscreen) ? 'none' : '';
        })

    return this;
}


ExchangeLayer.prototype.onExchangeMouseOver = function(arg) {
    if (!arg) return this.exchangeMouseOverHandler;
    else this.exchangeMouseOverHandler = arg;
    return this;
};

ExchangeLayer.prototype.onExchangeMouseMove = function(arg) {
    if (!arg) return this.exchangeMouseMoveHandler;
    else this.exchangeMouseMoveHandler = arg;
    return this;
};

ExchangeLayer.prototype.onExchangeMouseOut = function(arg) {
    if (!arg) return this.exchangeMouseOutHandler;
    else this.exchangeMouseOutHandler = arg;
    return this;
};

ExchangeLayer.prototype.co2color = function(arg) {
    if (!arg) return this._co2color;
    else this._co2color = arg;
    return this;
};

ExchangeLayer.prototype.data = function(arg) {
    if (!arg) return this._data;
    else {
        this._data = arg;
    }
    return this;
};

module.exports = ExchangeLayer;
