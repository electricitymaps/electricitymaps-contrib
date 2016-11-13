function ExchangeLayer(selector) {
    this.TRIANGLE_HEIGHT = 1.0;
    this.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT = 0.2;
    this.STROKE_CO2_THRESHOLD = 550;
    this.exchangeAnimationDurationScale = d3.scale.pow()
        .exponent(2)
        .domain([500, 6000])
        .range([2000, 10]);

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

    var that = this;
    this.animateGradient = function(selector, colorAccessor, durationAccessor) {
        var color = colorAccessor();
        var arrow = selector.selectAll('stop')
            .data([
                {offset: 0, color: color},
                {offset: 0, color: color},
                {offset: 0, color: d3.rgb(color).hsl().l > 0.1 ? d3.rgb(color).brighter(2) : d3.rgb('lightgray')},
                {offset: 0, color: color},
                {offset: 1, color: color},
            ]);
        arrow.enter()
            .append('stop')
            .attr('stop-color', function(d) { return d.color; })
        arrow
            .transition()
            .attr('stop-color', function(d) { return d.color; })
            .duration(durationAccessor())
            .ease('linear')
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
            .each('end', function (d, i) {
                // We should only start one animation, so just wait for the
                // first transition to finish
                if (i == 0)
                    return that.animateGradient(selector, colorAccessor, durationAccessor);
            });
    };
}

ExchangeLayer.prototype.projection = function(arg) {
    if (!arg) return this._projection;
    else this._projection = arg;
    return this;
};

ExchangeLayer.prototype.render = function() {
    if (!this._data) { return; }
    var that = this;
    var exchangeGradients = this.exchangeGradientsContainer
        .selectAll('.exchange-gradient')
        .data(this._data)
    exchangeGradients.enter()
        .append('linearGradient')
        .attr('class', 'exchange-gradient')
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', 0).attr('y1', -2.0 * this.TRIANGLE_HEIGHT - 1)
        .attr('x2', 0).attr('y2', this.TRIANGLE_HEIGHT + 1)
        .attr('id', function (d, i) { return 'exchange-gradient-' + i; });

    var getTransform = function (d) {
        var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
        var scale = 4.5;
        return 'rotate(' + rotation + '), scale(' + scale + ')';
    };
    var exchangeArrows = this.exchangeArrowsContainer
        .selectAll('.exchange-arrow')
        .data(this._data, function(d) { return d.countryCodes[0] + '-' + d.countryCodes[1]; });
    exchangeArrows.enter()
        .append('g') // Add a group so we can animate separately
        .attr('class', 'exchange-arrow')
        .append('path')
            .attr('d', function(d) { return that.trianglePath(); })
            .attr('fill', function (d, i) { return 'url(#exchange-gradient-' + i + ')'; })
            .attr('stroke-width', 0.1)
            .attr('transform', getTransform)
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
                        return co2color(d.co2intensity);
                    },
                    function() {
                        if (!d.netFlow) return 2000; // we have to return a duration
                        return that.exchangeAnimationDurationScale(Math.abs(d.netFlow));
                    }
                );
            })
    exchangeArrows
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

ExchangeLayer.prototype.data = function(arg) {
    if (!arg) return this._data;
    else {
        this._data = arg;
    }
    return this;
};
