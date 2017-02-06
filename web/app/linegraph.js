d3 = require('d3');
moment = require('moment');

function LineGraph(selector, xAccessor, yAccessor, definedAccessor, yColorScale) {
    this.rootElement = d3.select(selector);
    this.graphElement = this.rootElement.append('g');
    this.interactionRect = this.graphElement.append('rect')
        .style('opacity', 0)
        .style('width', '100%')
        .style('height', '100%');
    this.verticalLine = this.rootElement.append('line')
        .style('display', 'none')
        .style('pointer-events', 'none')
        .style('stroke-width', 1)
        .style('stroke', 'lightgrey');
    this.markerElement = this.rootElement.append('circle')
        .style('fill', 'lightgrey')
        .style('pointer-events', 'none')
        .attr('r', 4)
        .style('display', 'none');

    this.xAccessor = xAccessor;
    this.yAccessor = yAccessor;
    this.definedAccessor = definedAccessor;

    // Create axis
    this.xAxisElement = this.rootElement.append('g')
        .attr('class', 'x axis');

    // Create scales
    this.x = x = d3.scaleTime();
    this.y = y = d3.scaleLinear()
        .domain(d3.extent(yColorScale.domain()));

    // Create line
    this.line = d3.line()
        .x(function(d, i) { return x(xAccessor(d, i)); })
        .y(function(d, i) { return y(yAccessor(d, i)); })
        .defined(definedAccessor)
        .curve(d3.curveMonotoneX);
}

LineGraph.prototype.data = function (arg) {
    if (!arg) return this._data;
    if (!arg.length) {
        this._data = [];
        return this;
    }

    this._data = data = arg;

    // Set domains
    this.x.domain(d3.extent(data, this.xAccessor));

    return this;
}

LineGraph.prototype.render = function () {
    // Convenience
    var that = this,
        x = this.x,
        y = this.y,
        z = this.z,
        stack = this.stack,
        data = this._data;

    // Set scale range, based on effective pixel size
    var width  = this.rootElement.node().getBoundingClientRect().width,
        height = this.rootElement.node().getBoundingClientRect().height;
    var X_AXIS_HEIGHT = 20;
    var X_AXIS_PADDING = 4;
    x.range([0, width]);
    y.range([height, X_AXIS_HEIGHT + X_AXIS_PADDING]);

    this.verticalLine
        .attr('y1', 0)
        .attr('y2', height);

    var selection = this.graphElement
        .selectAll('.layer')
        .data([data]) // only one time series for now
    var layer = selection.enter().append('g')
        .attr('class', 'layer');

    layer.append('path')
        .attr('class', 'line')
        .style('fill', 'none')
        .style('stroke', 'lightgrey')
        .style('stroke-width', 1)
        .style('pointer-events', 'none');
    layer.merge(selection).select('path.line')
        .attr('d', this.line);

    this.interactionRect
        .on('mouseover', function () {
            that.verticalLine.style('display', 'block');
            that.markerElement.style('display', 'block');
            if (that.mouseOverHandler)
                that.mouseOverHandler.call(this);
        })
        .on('mouseout', function () {
            that.verticalLine.style('display', 'none');
            that.markerElement.style('display', 'none');
            if (that.mouseOutHandler)
                that.mouseOutHandler.call(this);
        })
        .on('mousemove', function () {
            var dx = d3.event.x - this.getBoundingClientRect().left;
            var datetime = x.invert(dx);
            // Find data point closest to
            var i = d3.bisectLeft(data.map(that.xAccessor), datetime);
            if (i > 0 && datetime - that.xAccessor(data[i-1]) < that.xAccessor(data[i]) - datetime)
                i--;
            that.verticalLine
                .attr('x1', x(that.xAccessor(data[i])))
                .attr('x2', x(that.xAccessor(data[i])));
            that.markerElement
                .attr('cx', x(that.xAccessor(data[i])))
                .attr('cy', y(that.yAccessor(data[i])));
            if (that.mouseMoveHandler)
                that.mouseMoveHandler.call(this, data[i]);
        });

    // x axis
    var xAxis = d3.axisTop(x)
        .ticks(6)
        .tickFormat(function(d) { return moment(d).format('LT'); });
    this.xAxisElement
        .transition()
        .style('transform', 'translate(0, ' + X_AXIS_HEIGHT + 'px)')
        .call(xAxis);

    return this;
}

LineGraph.prototype.onMouseOver = function(arg) {
    if (!arg) return this.mouseOverHandler;
    else this.mouseOverHandler = arg;
    return this;
}
LineGraph.prototype.onMouseOut = function(arg) {
    if (!arg) return this.mouseOutHandler;
    else this.mouseOutHandler = arg;
    return this;
}
LineGraph.prototype.onMouseMove = function(arg) {
    if (!arg) return this.mouseMoveHandler;
    else this.mouseMoveHandler = arg;
    return this;
}

module.exports = LineGraph;
