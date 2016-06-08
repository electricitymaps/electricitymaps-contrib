function HorizontalColorbar(selector, d3scale, d3TickFormat, d3TickValues) {
    this.PADDING = 20; // Inner padding allow place for the axis

    this.root = d3.select(selector);
    this.scale = d3scale.copy();
    this.width = this.root.node().getBoundingClientRect().width;
    this.height = this.root.node().getBoundingClientRect().height;

    this.colorbarWidth = this.width - 2 * this.PADDING;
    this.colorbarHeight = this.height - this.PADDING;

    this.gColorbar = this.root.append('g')
        .attr('transform', 'translate(' + this.PADDING + ', 0)');

    if (this.scale.ticks) {
        // Linear scale
        this.scale = d3.scale.linear()
            .range([0, this.colorbarWidth])
            .domain(d3.extent(d3scale.domain()));
        this.gGradient = this.gColorbar.append('linearGradient')
            .attr('id', selector + 'gradient')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', '100%')
            .attr('y2', 0)

        // Place the colors on the gradient
        var that = this;
        this.gGradient.selectAll('stop')
            .data(d3scale.range())
            .enter()
                .append('stop')
                .attr('class', 'stop')
                .attr('offset', function (d, i) { 
                    return i * 1.0 / (d3scale.range().length - 1);
                })
                .attr('stop-color', function (d) { return d; });
        // Add a rect with the gradient
        this.gColorbar.append('rect')
            .attr('width', this.colorbarWidth)
            .attr('height', this.colorbarHeight)
            .style('fill', 'url(#' + selector + 'gradient' + ')');
    } else {
        // Ordinal scale
        this.scale.rangeBands([0, this.colorbarWidth]);
        this.deltaOrdinal = this.colorbarWidth / this.scale.range().length;
        gColorbar.selectAll('rect')
            .data(this.scale.range())
            .enter()
                .append('rect')
                .attr('x', i * this.deltaOrdinal)
                .attr('width', this.deltaOrdinal)
                .attr('y', 0)
                .attr('height', this.colorbarHeight)
                .style('fill', d3.identity)
    }

    // Draw a container around the colorbar
    this.gColorbar.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', this.colorbarWidth)
        .attr('height', this.colorbarHeight)
        .style('fill', 'none')
        .style('stroke', 'gray')
        .style('stroke-width', 1)
        .attr('shape-rendering', 'crispEdges');

    // Draw the horizontal axis
    var axis = d3.svg.axis()
        .scale(this.scale);
    if (d3TickFormat)
        axis.tickFormat(d3TickFormat);
    if (d3TickValues)
        axis.tickValues(d3TickValues);
    
    this.gColorbarAxis = this.gColorbar.append('g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0, ' + (this.colorbarHeight) + ')')
        .call(axis)
    this.gColorbarAxis.selectAll('.tick text')
        .attr('fill', 'gray')
        .attr('transform', 'translate(0, ' + 4 + ')')
    this.gColorbarAxis.selectAll('.tick line')
            .style('stroke', 'gray')
            .style('stroke-width', 1)
            .attr('shape-rendering', 'crispEdges')
            .attr('y2', this.colorbarHeight / 2.0);
    this.gColorbarAxis.select('path')
            .style('fill', 'none')
            .style('stroke', 'none');

    // Prepare an invisible marker
    if (this.scale.ticks) {
        this.gColorbar.append('line')
            .attr('class', 'marker')
            .style('stroke', 'gray')
            .style('stroke-width', 3)
            .attr('y1', 0)
            .attr('y2', this.colorbarHeight)
            .style('display', 'none');
    } else {
        this.gColorbar.append('rect')
            .attr('class', 'marker')
            .style('stroke', 'gray')
            .style('stroke-width', 3)
            .style('fill', 'none')
            .attr('y', 0)
            .attr('width', this.deltaOrdinal)
            .style('display', 'none');
    }

    return this;
}

HorizontalColorbar.prototype.currentMarker = function(d) {
    if (d) {
        if (this.scale.ticks) {
            // Linear
            this.gColorbar.select('.marker')
                .attr('x1', this.scale(d))
                .attr('x2', this.scale(d))
                .style('display', 'block')
        } else {
            // Ordinal
            this.gColorbar.select('.marker')
                .attr('x', this.scale(d))
                .attr('width', this.delta)
                .style('display', 'block')
        }
    } else {
        this.gColorbar.select('.marker')
            .style('display', 'none')
    }
}

HorizontalColorbar.prototype.markerColor = function(arg) {
    this.gColorbar.select('.marker')
        .style('stroke', arg);
    return this;
}
