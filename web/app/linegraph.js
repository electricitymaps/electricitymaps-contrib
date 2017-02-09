d3 = require('d3');
moment = require('moment');

function LineGraph(selector, xAccessor, yAccessor, definedAccessor, yColorScale) {
    this.rootElement = d3.select(selector);
    this.graphElement = this.rootElement.append('g');
    this.interactionRect = this.graphElement.append('rect')
        .style('cursor', 'pointer')
        .style('opacity', 0);
    this.verticalLine = this.rootElement.append('line')
        .style('display', 'none')
        .style('pointer-events', 'none')
        .style('stroke-width', 1)
        .style('opacity', 0.3)
        .style('shape-rendering', 'crispEdges')
        .style('stroke', 'lightgrey');
    this.markerElement = this.rootElement.append('circle')
        .style('fill', 'lightgrey')
        .style('pointer-events', 'none')
        .attr('r', 5)
        .style('stroke', 'lightgrey')
        .style('stroke-width', 1);

    this.xAccessor = xAccessor;
    this.yAccessor = yAccessor;
    this.definedAccessor = definedAccessor;
    this.yColorScale = yColorScale;

    // Create axis
    this.xAxisElement = this.rootElement.append('g')
        .attr('class', 'x axis')
        .style('pointer-events', 'none');
    this.yAxisElement = this.rootElement.append('g')
        .attr('class', 'y axis')
        .style('pointer-events', 'none');

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

    // Interaction state
    this.frozen = false;
    this.selectedIndex;
}

LineGraph.prototype.data = function (arg) {
    if (!arg) return this._data;

    this._data = data = arg;

    // Cache xAccessor
    this.datetimes = data.map(this.xAccessor);

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
        data = this._data,
        datetimes = this.datetimes;

    // Set scale range, based on effective pixel size
    var width  = this.rootElement.node().getBoundingClientRect().width,
        height = this.rootElement.node().getBoundingClientRect().height;
    var X_AXIS_HEIGHT = 20;
    var X_AXIS_PADDING = 4;
    var Y_AXIS_WIDTH = 25;
    var Y_AXIS_PADDING = 4;
    x.range([0, width - Y_AXIS_WIDTH]);
    y.range([height - X_AXIS_HEIGHT, Y_AXIS_PADDING]);

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
        .style('opacity', 0.7)
        .style('pointer-events', 'none');
    layer.merge(selection).select('path.line')
        .attr('d', this.line);

    var i = this.selectedIndex || (data.length - 1);
    if (data.length && data[i] && that.definedAccessor(data[i])) {
        this.markerElement
            .style('display', 'block')
            .attr('cx', x(datetimes[i]))
            .attr('cy', y(that.yAccessor(data[i])))
            .style('fill', that.yColorScale(
                that.yAccessor(data[i])));
        that.verticalLine
            .attr('x1', x(datetimes[i]))
            .attr('x2', x(datetimes[i]));
    } else {
        this.markerElement.style('display', 'none');
    }

    this.verticalLine
        .attr('y1', y.range()[0])
        .attr('y2', y.range()[1]);

    isMobile = 
        (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);

    function drag() {
        if (!datetimes.length) return;
        var dx = d3.event.pageX ? (d3.event.pageX - this.getBoundingClientRect().left) :
            (d3.touches(this)[0][0]);
        var datetime = x.invert(dx);
        // Find data point closest to
        var i = d3.bisectLeft(datetimes, datetime);
        if (i > 0 && datetime - datetimes[i-1] < datetimes[i] - datetime)
            i--;
        if (i > datetimes.length - 1) i = datetimes.length - 1;
        that.selectedIndex = i;
        that.verticalLine
            .attr('x1', x(datetimes[i]))
            .attr('x2', x(datetimes[i]));
        if (!that.definedAccessor(data[i])) {
            // Not defined, hide the marker
            that.markerElement
                .style('display', 'none');
        } else {
            that.markerElement
                .style('display', 'block')
                .attr('cx', x(datetimes[i]))
                .attr('cy', y(that.yAccessor(data[i])))
                .style('fill', that.yColorScale(
                    that.yAccessor(data[i])));
        }
    }

    this.interactionRect
        .attr('x', x.range()[0])
        .attr('y', y.range()[1])
        .attr('width', x.range()[1] - x.range()[0])
        .attr('height', y.range()[0] - y.range()[1])
        .on(isMobile ? 'touchstart' : 'mouseover', function () {
            if (!datetimes.length) return;
            // Always unfreeze on mobile
            if (isMobile) {
                that.frozen = true; that.togglefreeze();
            }
            that.verticalLine.style('display', 'block');
            if (that.mouseOverHandler)
                that.mouseOverHandler.call(this);
        })
        .on(isMobile ? 'touchend' : 'mouseout', function () {
            if (!datetimes.length) return;
            if (that.frozen) return;
            // Always freeze on mobile
            if (isMobile) {
                that.frozen = false; that.togglefreeze();
                return;
            }
            that.verticalLine.style('display', 'none');
            if (that.definedAccessor(data[data.length - 1])) {
                that.markerElement
                    .style('display', 'block')
                    .attr('cx', x(datetimes[datetimes.length - 1]))
                    .attr('cy', y(that.yAccessor(data[data.length - 1])))
                    .style('fill', that.yColorScale(
                        that.yAccessor(data[data.length - 1])));
            } else {
                that.markerElement
                    .style('display', 'none');
            }
            if (that.mouseOutHandler)
                that.mouseOutHandler.call(this);
        })
        .on(isMobile ? 'touchmove' : 'mousemove', function () {
            if (that.frozen) return;
            drag.call(this);
            if (that.mouseMoveHandler)
                that.mouseMoveHandler.call(this, data[that.selectedIndex]);
        })
        .on('click', function() {
            if (!isMobile) {
                that.togglefreeze();
                if (!that.frozen) {
                    drag.call(this);
                    if (that.mouseMoveHandler)
                        that.mouseMoveHandler.call(this, data[that.selectedIndex]);
                }
            } else {
                drag.call(this);
                if (that.mouseMoveHandler)
                    that.mouseMoveHandler.call(this, data[that.selectedIndex]);
            }
        });

    // x axis
    var xAxis = d3.axisBottom(x)
        .ticks(6)
        .tickFormat(function(d) { return moment(d).format('LT'); });
    this.xAxisElement
        // Need to remove 1px in order to see the 1px line
        .style('transform', 'translate(0, ' + (height - X_AXIS_HEIGHT) + 'px)')
        .call(xAxis);

    // y axis
    var yAxis = d3.axisRight(y)
        .ticks(6);
    this.yAxisElement
        .style('transform', 'translate(' + (width - Y_AXIS_WIDTH) + 'px, 0)')
        .call(yAxis);

    return this;
}

LineGraph.prototype.togglefreeze = function() {
    this.frozen = !this.frozen;
    if (!this.frozen) this.selectedIndex = undefined;
    this.markerElement.style('stroke',
        this.frozen ? 'black' : 'lightgrey');
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
