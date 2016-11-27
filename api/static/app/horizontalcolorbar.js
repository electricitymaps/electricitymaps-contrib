function HorizontalColorbar(selector, d3ColorScale, d3TickFormat, d3TickValues) {
    this.PADDING_X = 10; // Inner padding allow place for the axis text

    this.root = d3.select(selector);
    this.scale = d3ColorScale.copy();
    this.colors = d3ColorScale.range();
    this.d3TickFormat = d3TickFormat;
    this.d3TickValues = d3TickValues;

    this.gColorbar = this.root.append('g')
        .attr('transform', 'translate(' + this.PADDING_X + ', 0)');
    
    if (this.scale.ticks) {
        // Linear scale

        // Create gradient
        this.gGradient = this.gColorbar.append('linearGradient')
            .attr('id', selector + 'gradient')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', '100%')
            .attr('y2', 0)

        // Create fill
        this.gColorbar.append('rect')
            .attr('class', 'gradient')
            .style('fill', 'url(#' + selector + 'gradient' + ')');

        // Prepare an invisible marker
        this.gColorbar.append('line')
            .attr('class', 'marker')
            .style('stroke', 'gray')
            .style('stroke-width', 2)
            .attr('y1', 0)
            .style('display', 'none');

    } else {
        // Ordinal scale

        // Prepare an invisible marker
        this.gColorbar.append('rect')
            .attr('class', 'marker')
            .style('stroke', 'gray')
            .style('stroke-width', 2)
            .style('fill', 'none')
            .attr('y', 0)
            .style('display', 'none');
    }

    // Draw a container around the colorbar
    this.gColorbar.append('rect')
        .attr('class', 'border')
        .attr('x', 0)
        .attr('y', 0)
        .style('fill', 'none')
        .style('stroke', 'gray')
        .style('stroke-width', 1)
        .attr('shape-rendering', 'crispEdges');

    // Prepare axis
    this.gColorbarAxis = this.gColorbar.append('g');

    return this;
}

HorizontalColorbar.prototype.render = function() {
    this.width = this.root.node().getBoundingClientRect().width;
    this.height = this.root.node().getBoundingClientRect().height;

    this.colorbarWidth = this.width - 2 * this.PADDING_X;
    this.colorbarHeight = this.height - 2 * this.PADDING_X;

    var that = this;

    if (this.scale.ticks) {
        // Linear scale
        this.scale
            .range(d3.range(this.colors.length).map(function (d, i) {
                return d3.interpolate(0, that.colorbarWidth)(i / (that.colors.length - 1));
            }));

        // Place the colors on the gradient
        var selector = this.gGradient.selectAll('stop')
            .data(this.colors);
        selector.enter()
            .append('stop')
        selector
            .attr('offset', function (d, i) { 
                return i / (that.colors.length - 1);
            })
            .attr('stop-color', function (d) { return d; });
        // Add a rect with the gradient
        this.gColorbar.select('rect.gradient')
            .attr('width', this.colorbarWidth)
            .attr('height', this.colorbarHeight);

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

    // Prepare an invisible marker
    if (this.scale.ticks) {
        this.gColorbar.select('line')
            .attr('y2', this.colorbarHeight)
    } else {
        this.gColorbar.select('rect')
            .attr('width', this.deltaOrdinal)
    }

    // Draw a container around the colorbar
    this.gColorbar.select('rect.border')
        .attr('width', this.colorbarWidth)
        .attr('height', this.colorbarHeight);

    // Draw the horizontal axis
    var axis = d3.svg.axis()
        .scale(this.scale)
        .innerTickSize(this.colorbarHeight / 2.0)
        .tickPadding(3);
    if (this.d3TickFormat)
        axis.tickFormat(this.d3TickFormat);
    if (this.d3TickValues)
        axis.tickValues(this.d3TickValues);
    
    this.gColorbarAxis
        .attr('class', 'x axis')
        .attr('transform', 'translate(0, ' + (this.colorbarHeight) + ')')
        .call(axis)
    this.gColorbarAxis.selectAll('.tick text')
        .attr('fill', 'gray');
    this.gColorbarAxis.selectAll('.tick line')
            .style('stroke', 'gray')
            .style('stroke-width', 1)
            .attr('shape-rendering', 'crispEdges')
    this.gColorbarAxis.select('path')
            .style('fill', 'none')
            .style('stroke', 'none');

    return this;
}

HorizontalColorbar.prototype.currentMarker = function(d) {
    if (d !== undefined) {
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
