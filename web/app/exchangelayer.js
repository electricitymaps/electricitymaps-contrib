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
    this.exchangeGradientsContainer = this.root.append('g');

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

ExchangeLayer.prototype.renderOne = function(selector) {
    var element = d3.select(selector);
    var id = String(parseInt(Math.random()*10000));
    var gradient = appendGradient(
        element.append('g').attr('class', 'exchange-gradient'),
        this.TRIANGLE_HEIGHT
    ).attr('id', id);
    var that = this;
    element
        .append('path')
        .attr('d', function(d) { return that.trianglePath(); })
        .attr('fill', function (d, i) { 
            return 'url(#' + id + ')';
        })
        .attr('transform-origin', '0 0')
        .style('transform', 'translate(6px,8px) scale(4.5) rotate(-90deg)')

    return element;
};

ExchangeLayer.prototype.render = function() {
    if (!this._data) { return; }
    var that = this;
    var exchangeGradients = this.exchangeGradientsContainer
        .selectAll('.exchange-gradient')
        .data(this._data)
    exchangeGradients.exit().remove();

    var exchangeArrows = this.exchangeArrowsContainer
        .selectAll('.exchange-arrow')
        .data(this._data, function(d) { return d.countryCodes[0] + '-' + d.countryCodes[1]; });
    exchangeArrows.exit().remove();
    // This object refers to arrows created
    // Add all static properties
    var newArrows = exchangeArrows.enter()
        .append('div') // Add a group so we can animate separately
        .attr('class', 'exchange-arrow');
    newArrows.append('img')
        .attr('width', 49)
        .attr('height', 81)
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
    var arrowCarbonIntensitySliceSize = 80; // New arrow color at every X rise in co2
    var maxCarbonIntensity = 800; // we only have arrows up to a certain point
    // Calculate arrow scale
    // Note: the scaling should be based on the same metric as countryMap
    this.arrowScale(this.root.node().parentNode.getBoundingClientRect().height / 4000);

    // This object refers to all arrows
    // Here we add all dynamic properties (i.e. that depend on data)
    newArrows.merge(exchangeArrows)
        .style('display', function (d) {
            return (d.netFlow || 0) == 0 ? 'display:none;' : '';
        })
        .style('transform', function (d) {
            var center = that.projection()(d.lonlat);
            var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
            return 'translateX(' + center[0] + 'px) translateY(' + center[1] + 'px) rotate(' + rotation + 'deg)';
        })
        .select('img')
        .style('transform', 'scale(' + this.arrowScale() + ')')
        .attr('src', function (d) {
            var intensity = Math.min(maxCarbonIntensity, Math.floor(d.co2intensity - d.co2intensity%arrowCarbonIntensitySliceSize));
            if(isNaN(intensity)) intensity = 'nan';
            return 'images/arrow-'+intensity+'-animated-'+that.exchangeAnimationDurationScale(Math.abs(d.netFlow || 0))+'.gif';
        });

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
