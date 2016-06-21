function ExchangeLayer(selector) {
    this.TRIANGLE_HEIGHT = 1.0;
    this.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT = 0.2;
    this.exchangeAnimationDurationScale = d3.scale.pow()
        .exponent(2)
        .domain([500, 4000])
        .range([2000, 10])
    this.exchangeArrowScale = d3.scale.pow()
        .exponent(2)
        .domain([500, 4000])
        .range([4, 15])

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
    this.animateGradient = function(selector, color, duration) {
        var arrow = selector.selectAll('stop')
            .data([
                {offset: 0, color: color},
                {offset: 0, color: color},
                {offset: 0, color: d3.rgb(color).brighter(2.0)},
                {offset: 0, color: color},
                {offset: 1, color: color},
            ]);
        arrow.enter().append('stop')
            .attr('offset', function(d) { return d.offset; })
            .attr('stop-color', function(d) { return d.color; })
        arrow
            .transition()
            .duration(duration)
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
            .each('end', function () { 
                return that.animateGradient(selector, color, duration);
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
    var exchangeGradients = this.exchangeGradientsContainer.selectAll('.exchange-gradient')
        .data(this._data)
    exchangeGradients.enter()
        .append('linearGradient')
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', 0).attr('y1', -2.0 * this.TRIANGLE_HEIGHT - 1)
        .attr('x2', 0).attr('y2', this.TRIANGLE_HEIGHT + 1)
        .attr('id', function (d, i) { return 'exchange-gradient-' + i; });

    var exchangeArrows = this.exchangeArrowsContainer.selectAll('.exchange-arrow')
        .data(this._data);
    exchangeArrows.enter()
        .append('path')
        .attr('class', 'exchange-arrow')
        .attr('d', function(d) { return that.trianglePath(); })
        .attr('fill', function (d, i) { return 'url(#exchange-gradient-' + i + ')' })
        .attr('stroke', 'black')
        .attr('stroke-width', 0.1)
        .on('click', function (d) { console.log(d); })
    exchangeArrows
        .attr('transform', function (d) {
            var rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
            var scale = that.exchangeArrowScale(Math.abs(d.netFlow));
            var center = that.projection()(d.lonlat);
            return 'translate(' + center[0] + ',' + center[1] + '),' + 
                'rotate(' + rotation + '), scale(' + scale + ')';
        })
        .each(function (d, i) {
            if (!d.netFlow) return;
            var co2 = d.co2()[d.netFlow > 0 ? 0 : 1];
            return that.animateGradient(
                d3.select('#exchange-gradient-' + i), 
                co2 ? co2color(co2) : 'grey',
                that.exchangeAnimationDurationScale(Math.abs(d.netFlow))
            );
        });

    return this;
}

ExchangeLayer.prototype.data = function(arg) {
    if (!arg) return this._data;
    else {
        this._data = arg;
    }
    return this;
};
