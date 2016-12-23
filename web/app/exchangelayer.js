var d3 = require('d3');

function ExchangeLayer(selector, co2Color) {
    this.TRIANGLE_HEIGHT = 1.0;
    this.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT = 0.2;
    this.STROKE_CO2_THRESHOLD = 550;
    this.exchangeAnimationDurationScale = d3.scalePow()
        .exponent(2)
        .domain([500, 6000])
        .range([2000, 10]);
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

    function isMobile() {
        return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
    }

    var that = this;
    this.animateGradient = function(selector, colorAccessor, durationAccessor) {
        var color = colorAccessor();
        var arrow = selector.selectAll('stop')
            .data([
                {offset: 0, color: color},
                {offset: 0, color: color},
                {offset: 0, color: d3.hsl(d3.rgb(color)).l > 0.1 ? d3.rgb(color).brighter(2) : d3.rgb('lightgray')},
                {offset: 0, color: color},
                {offset: 1, color: color},
            ]);
        var arrowEnter = arrow.enter()
            .append('stop')
            .attr('stop-color', function(d) { return d.color; });

        if (!isMobile()) {
            arrowEnter.merge(arrow)
                .transition()
                .attr('stop-color', function(d) { return d.color; })
                .duration(durationAccessor())
                .ease(d3.easeLinear)
                .attrTween('offset', function(d, i, a) {
                    // Only animate the middle color
                    if (i == 0 || i == 4)
                        return function (t) { return d.offset };
                    else {
                        return function (t) {
                            return t + (i - 2) * that.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT;
                        };
                    }
                })
                .on('end', function (d, i) {
                    // We should only start one animation, so just wait for the
                    // first transition to finish
                    if (i == 0)
                        return that.animateGradient(selector, colorAccessor, durationAccessor);
                });
        }
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

var getTransform = function(d) {
    var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
    var scale = 4.5;
    return 'rotate(' + rotation + '), scale(' + scale + ')';
};

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
        .attr('fill', function (d, i) { return 'url(#' + id + ')'; })
        .attr('transform-origin', '0 0')
        .style('transform', 'translate(6px,8px) scale(4.5) rotate(-90deg)')

    this.animateGradient(gradient, 
        function() { return 'orange'; }, 
        function() { return that.exchangeAnimationDurationScale(1000); });

    return element
};

ExchangeLayer.prototype.render = function() {
    if (!this._data) { return; }
    var that = this;
    var exchangeGradients = this.exchangeGradientsContainer
        .selectAll('.exchange-gradient')
        .data(this._data)
    appendGradient(exchangeGradients.enter(), this.TRIANGLE_HEIGHT)
        .attr('id', function (d, i) { return 'exchange-gradient-' + i; });

    var exchangeArrows = this.exchangeArrowsContainer
        .selectAll('.exchange-arrow')
        .data(this._data, function(d) { return d.countryCodes[0] + '-' + d.countryCodes[1]; });
    var newArrows = exchangeArrows.enter()
        .append('g') // Add a group so we can animate separately
        .attr('class', 'exchange-arrow')
    newArrows.append('path')
            .attr('d', function(d) { return that.trianglePath(); })
            .attr('fill', function (d, i) { return 'url(#exchange-gradient-' + i + ')'; })
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
            .on('click', function (d) { console.log(d); })
            .each(function (d, i) {
                // Warning: with this technique, we can add arrows dynamically,
                // but we can't remove them because we can't remove the animation.
                // This forces us to create them even though the netFlow could be 
                // null (and we should therefore hide the arrow), and thus
                // we have to have an animateGradient loop that access the related 
                // variables through accessors.
                return that.animateGradient(
                    d3.select('#exchange-gradient-' + i), 
                    function() {
                        var d = that.data()[i];
                        if (!d.co2intensity || !d.netFlow) return 'gray';
                        return that.co2Color(d.co2intensity);
                    },
                    function() {
                        if (!d.netFlow) return 2000; // we have to return a duration
                        return that.exchangeAnimationDurationScale(Math.abs(d.netFlow));
                    }
                );
            })
    newArrows.merge(exchangeArrows)
        .attr('transform', function (d) {
            var center = that.projection()(d.lonlat);
            return 'translate(' + center[0] + ',' + center[1] + ')';
        })
        .attr('stroke', function (d, i) {
            if (!d.co2intensity) return 'lightgray';
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
