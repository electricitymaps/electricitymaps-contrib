var d3 = require('d3');

function ExchangeLayer(selector, co2Color) {
    this.TRIANGLE_HEIGHT = 1.0;
    this.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT = 0.2;
    this.STROKE_CO2_THRESHOLD = 550;
    this.exchangeAnimationDurationScale = d3.scaleLinear()
        .domain([500, 5000])
        .range([1500, 50])
        .clamp(true);
    this.co2Color = co2Color;

    this.root = d3.select(selector);
    this.exchangeArrowsContainer = this.root.append('g');
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

ExchangeLayer.prototype.animateGradient = function(element, color, duration) {
    var that = this;
    var stops = element.selectAll('stop')
        .data(d3.range(5));
    var newStops = stops.enter()
        .append('stop')
        newStops.merge(stops)
            .transition()
            .on('start', function repeat() {
                d3.active(this)
                    .attr('stop-color', function(i) { 
                        if (i == 2) {
                            if (d3.hsl(d3.rgb(color)).l > 0.2)
                                return d3.rgb(color).brighter(2);
                            else
                                return d3.rgb('lightgray');
                        } else
                            return color;
                    })
                    .transition()
                    .duration(duration)
                    .ease(d3.easeLinear)
                    .attrTween('offset', function(i, _, a) {
                        // Only animate the middle color
                        if (i == 0 || i == 4)
                            return function (t) { return i == 4 ? 1 : 0; };
                        else {
                            return function (t) {
                                return t + (i - 2) * that.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT;
                            };
                        }
                    })
                    .on('start', repeat);
            });
}

function isMobile() {
    return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
}

function getTransform(d) {
    var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
    var scale = 4.5;
    return 'rotate(' + rotation + '), scale(' + scale + ')';
};

ExchangeLayer.prototype.renderOne = function(selector) {
    var color = 'orange';

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
            return isMobile() ? color : 'url(#' + id + ')';
        })
        .attr('transform-origin', '0 0')
        .style('transform', 'translate(6px,8px) scale(4.5) rotate(-90deg)')

    if (!isMobile())
        that.animateGradient(gradient, color, 2000);

    return element;
};

ExchangeLayer.prototype.render = function() {
    if (!this._data) { return; }
    var that = this;
    var exchangeGradients = this.exchangeGradientsContainer
        .selectAll('.exchange-gradient')
        .data(this._data)
    exchangeGradients.exit().remove();
    var newGradients = appendGradient(exchangeGradients.enter(), this.TRIANGLE_HEIGHT)
        .attr('id', function (d, i) { return 'exchange-gradient-' + i; });

    var animate = !isMobile();
    
    if (animate) {
        // Add animations
        var gradients = newGradients.merge(exchangeGradients);
        gradients.each(function(d) {
            var color = (d.co2intensity && d.netFlow) && that.co2Color(d.co2intensity) || 'gray';
            var duration = d.netFlow && that.exchangeAnimationDurationScale(Math.abs(d.netFlow)) || 2000;
            that.animateGradient(d3.select(this), color, duration);
        });
    }

    var exchangeArrows = this.exchangeArrowsContainer
        .selectAll('.exchange-arrow')
        .data(this._data, function(d) { return d.countryCodes[0] + '-' + d.countryCodes[1]; });
    exchangeArrows.exit().remove();
    var newArrows = exchangeArrows.enter()
        .append('g') // Add a group so we can animate separately
        .attr('class', 'exchange-arrow')
    newArrows
        .append('path')
            .attr('d', function(d) { return that.trianglePath(); })
            .attr('fill', function (d, i) { 
                var color = (d.co2intensity && d.netFlow) && that.co2Color(d.co2intensity) || 'gray';
                return !animate ? color : 'url(#exchange-gradient-' + i + ')';
            })
            .attr('stroke-width', 0.1)
            .attr('transform', getTransform)
            .attr('transform-origin', '0 0')
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
    newArrows.merge(exchangeArrows)
        .attr('transform', function (d) {
            var center = that.projection()(d.lonlat);
            return 'translate(' + center[0] + ',' + center[1] + ')';
        })
        .attr('stroke', function (d, i) {
            if (!d.co2intensity) return 'black';
            return d.co2intensity > that.STROKE_CO2_THRESHOLD ? 'lightgray' : 'black';
        })
        .style('display', function (d) { return (d.netFlow || 0) == 0 ? 'none' : 'block'; })
        .select('path')
            .transition()
            .duration(2000)
            .attr('transform', getTransform);

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

ExchangeLayer.prototype.data = function(arg) {
    if (!arg) return this._data;
    else {
        this._data = arg;
    }
    return this;
};

module.exports = ExchangeLayer;
