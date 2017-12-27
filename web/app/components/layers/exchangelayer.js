var d3 = require('d3');

function ExchangeLayer(selector, arrowsSelector) {
    this.TRIANGLE_HEIGHT = 1.0;
    this.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT = 0.2;
    this.STROKE_CO2_THRESHOLD = 550;
    this.exchangeAnimationDurationScale = d3.scaleLinear()
        .domain([500, 5000])
        .range([1.5, 0])
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

ExchangeLayer.prototype.projection = function(arg) {
    if (!arg) return this._projection;
    else this._projection = arg;
    return this;
};

ExchangeLayer.prototype.render = function() {
    if (!this._data) { return; }
    // Abort if projection has not been set
    if (!this._projection) { return; }
    var that = this;

    let node = this.exchangeArrowsContainer.node();

    var mapWidth = parseInt(node.parentNode.getBoundingClientRect().width);
    var mapHeight = parseInt(node.parentNode.getBoundingClientRect().height);
    // Canvas needs to have it's width and height attribute set
    // this.exchangeArrowsContainer
    //     .style('width', mapWidth + 'px')
    //     .style('height', mapHeight + 'px');

    var exchangeArrows = this.exchangeArrowsContainer
        .selectAll('.exchange-arrow')
        .data(this._data, function(d) { return d; });
    exchangeArrows.exit().remove();

    // This object refers to arrows created
    // Add all static properties
    var newArrows = exchangeArrows.enter()
        .append('div') // Add a group so we can animate separately
        .attr('class', 'exchange-arrow');
    newArrows
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
        .on('click', function (d, i) {
            return that.exchangeClickHandler.call(this, d, i);
        });
    newArrows.append('img')
        .attr('class', 'base')
    newArrows.append('img')
        .attr('class', 'highlight')
        .attr('src', 'images/arrow-highlights/50.png');

    
    var arrowCarbonIntensitySliceSize = 80; // New arrow color at every X rise in co2
    var maxCarbonIntensity = 800; // we only have arrows up to a certain point

    var layerTransform = (this.exchangeArrowsContainer.style('transform') || "matrix(1, 0, 0, 1, 0, 0)")
        .replace(/matrix\(|\)/g, '').split(/\s*,\s*/);

    const merged = newArrows.merge(exchangeArrows)
        .style('display', function(d) {
            var arrowCenter = that.projection()(d.lonlat);
            var layerTranslateX = layerTransform[4];
            var mapScale = layerTransform[3];
            var centerX = (arrowCenter[0] * mapScale) - Math.abs(layerTranslateX);
            var isOffscreen = centerX < 0 || centerX > mapWidth;
            var hasLowFlow = (d.netFlow || 0) == 0;
            return (hasLowFlow || isOffscreen) ? 'none' : '';
        })
        .style('transform', function (d) {
            var center = that.projection()(d.lonlat);
            var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
            return 'translateX(' + center[0] + 'px) translateY(' + center[1] + 'px) rotate(' + rotation + 'deg) scale(0.2)';
        })
    merged.select('img.highlight')
            .style('animation-duration', d =>
                that.exchangeAnimationDurationScale(Math.abs(d.netFlow || 0)) + 's');
    merged.select('img.base')
        .attr('src', function (d) {
            var intensity = Math.min(maxCarbonIntensity, Math.floor(d.co2intensity - d.co2intensity%arrowCarbonIntensitySliceSize));
            if (d.co2intensity == null || isNaN(intensity)) intensity = 'nan';
            return 'images/arrow-' + intensity + '-outline.png';
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

ExchangeLayer.prototype.onExchangeClick = function(arg) {
    if (!arg) return this.exchangeClickHandler;
    else this.exchangeClickHandler = arg;
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
