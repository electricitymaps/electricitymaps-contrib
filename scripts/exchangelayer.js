function ExchangeLayer(selector, projection) {
    this.TRIANGLE_HEIGHT = 8;

    this.root = d3.select(selector);
    this.exchangeArrowsContainer = this.root.append('g');
    this.exchangeGradientsContainer = this.root.append('g');

    this.trianglePath = function(w) {
        return 'M 0 0 L ' + w + ' ' + this.TRIANGLE_HEIGHT + ' L -' + w + ' ' + this.TRIANGLE_HEIGHT + ' Z ' +
        'M 0 -' + this.TRIANGLE_HEIGHT + ' L ' + w + ' 0 L -' + w + ' 0 Z ' +
        'M 0 -' + this.TRIANGLE_HEIGHT * 2.0 + ' L ' + w + ' -' + this.TRIANGLE_HEIGHT + ' L -' + w + ' -' + this.TRIANGLE_HEIGHT + ' Z'
    };
}

ExchangeLayer.prototype.data = function(arg) {
    if (!arg) return this.data;
    else {
        this.data = arg;

        let that = this;
        let exchangeGradients = this.exchangeGradientsContainer.selectAll('.exchange-gradient')
            .data(this.data)
            .enter()
            .append('linearGradient')
            .attr('gradientUnits', 'userSpaceOnUse')
            .attr('x1', 0).attr('y1', -2.0 * this.TRIANGLE_HEIGHT - 5)
            .attr('x2', 0).attr('y2', this.TRIANGLE_HEIGHT + 5)
            .attr('id', function (d, i) { return 'exchange-gradient-' + i; });

        let exchangeArrows = this.exchangeArrowsContainer.selectAll('.exchange-arrow')
            .data(this.data)
            .enter()
            .append('path')
            .attr('class', 'exchange-arrow')
            .attr('d', function(d) { 
                return that.trianglePath(exchangeArrowWidthScale(Math.abs(d.netFlow)));
            })
            .attr('transform', function (d) {;
                let rotation = d.rotation + (d.netFlow < 0 ? 180 : 0);
                return 'translate(' + d.center[0] + ',' + d.center[1] + '),rotate(' + rotation + ')';
            })
            .attr('fill', function (d, i) { return 'url(#exchange-gradient-' + i + ')' })
            .attr('stroke', function (d) { return d.netFlow ? 'black' : 'none'; })
            .attr('stroke-width', 0.4)
            .on('click', function (d) { console.log(d, exchangeAnimationScale(Math.abs(d.netFlow))); })
            .each(function (d, i) {
                if (!d.netFlow) return;
                let co2 = d.co2[d.netFlow > 0 ? 0 : 1];
                return animateGradient(
                    d3.select('#exchange-gradient-' + i), 
                    co2 ? co2color(co2) : 'grey',
                    exchangeAnimationScale(Math.abs(d.netFlow))
                );
            });
    }
    return this;
};
