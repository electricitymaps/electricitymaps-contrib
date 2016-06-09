function ExchangeLayer(selector, projection) {
    this.TRIANGLE_HEIGHT = 1;
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
        var w = this.TRIANGLE_HEIGHT;
        return 'M 0 0 L ' + w + ' ' + this.TRIANGLE_HEIGHT + ' L -' + w + ' ' + this.TRIANGLE_HEIGHT + ' Z ' +
        'M 0 -' + this.TRIANGLE_HEIGHT + ' L ' + w + ' 0 L -' + w + ' 0 Z ' +
        'M 0 -' + this.TRIANGLE_HEIGHT * 2.0 + ' L ' + w + ' -' + this.TRIANGLE_HEIGHT + ' L -' + w + ' -' + this.TRIANGLE_HEIGHT + ' Z'
    };

    var that = this;
    this.animateGradient = function(selector, color, duration) {
        var arrow = selector.selectAll('stop')
            .data([
                {offset: 0, color: color},
                {offset: 0, color: color},
                {offset: 0, color: d3.rgb(color).brighter(0.8)},
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
                        return 1 - t + (i - 2) * that.GRADIENT_ANIMATION_MIDDLE_WIDTH_COEFFICIENT;
                    };
                }
            })
            .each('end', function () { 
                return that.animateGradient(selector, color, duration);
            });
    };
}

ExchangeLayer.prototype.data = function(arg) {
    if (!arg) return this.data;
    else {
        this.data = arg;

        var that = this;
        var exchangeGradients = this.exchangeGradientsContainer.selectAll('.exchange-gradient')
            .data(this.data)
            .enter()
            .append('linearGradient')
            .attr('gradientUnits', 'userSpaceOnUse')
            .attr('x1', 0).attr('y1', -2.0 * this.TRIANGLE_HEIGHT - 1)
            .attr('x2', 0).attr('y2', this.TRIANGLE_HEIGHT + 1)
            .attr('id', function (d, i) { return 'exchange-gradient-' + i; });

        var exchangeArrows = this.exchangeArrowsContainer.selectAll('.exchange-arrow')
            .data(this.data)
            .enter()
            .append('path')
            .attr('class', 'exchange-arrow')
            .attr('d', function(d) { 
                return that.trianglePath();
            })
            .attr('transform', function (d) {;
                var rotation = d.rotation + (d.netFlow < 0 ? 180 : 0);
                return 'translate(' + d.center[0] + ',' + d.center[1] + '),' + 
                    'scale(' + that.exchangeArrowScale(Math.abs(d.netFlow)) + '),' + 
                    'rotate(' + rotation + ')';
            })
            .attr('fill', function (d, i) { return 'url(#exchange-gradient-' + i + ')' })
            .attr('stroke', function (d) { return d.netFlow ? 'black' : 'none'; })
            .attr('stroke-width', 0.1)
            .on('click', function (d) {
                console.log(d, that.exchangeAnimationDurationScale(Math.abs(d.netFlow)));
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
    }
    return this;
};
