'use strict'

var d3 = require('d3');
var moment = require('moment');

function AreaGraph(selector, modeColor, modeOrder) {
    this.rootElement = d3.select(selector);
    this.graphElement = this.rootElement.append('g');
    this.verticalLine = this.rootElement.append('line')
        .style('display', 'none')
        .style('pointer-events', 'none')
        .style('stroke-width', 1)
        .style('stroke', 'lightgrey');

    // Create axis
    this.xAxisElement = this.rootElement.append('g')
        .attr('class', 'x axis')
        .style('pointer-events', 'none');
    this.yAxisElement = this.rootElement.append('g')
        .attr('class', 'y axis')
        .style('pointer-events', 'none');

    // Create scales
    this.x = d3.scaleTime();
    this.y = d3.scaleLinear();
    this.z = d3.scaleOrdinal();

    // Other variables
    this.modeColor = modeColor;
    this.modeOrder = modeOrder;
}

AreaGraph.prototype.data = function (arg) {
    if (!arg) return this._data;
    if (!arg.length) {
        this._data = [];
        return this;
    }

    var that = this;

    // Parse data
    var exchangeKeysSet = this.exchangeKeysSet = d3.set();
    this._data = arg.map(function(d) {
        var obj = {
            datetime: moment(d.stateDatetime).toDate()
        };
        // Add production
        d3.entries(d.production).forEach(function(o) { obj[o.key] = o.value; });
        // Add exchange
        d3.entries(d.exchange).forEach(function(o) {
            exchangeKeysSet.add(o.key);
            obj[o.key] = Math.max(0, o.value);
        });
        // Keep a pointer to original data
        obj._countryData = d;
        return obj;
    });

    // Prepare stack
    var keys = this.modeOrder
        .concat(exchangeKeysSet.values())
    this.stack = d3.stack()
        .order(d3.stackOrderReverse)
        .offset(d3.stackOffsetDiverging)
        .keys(keys);

    // Set domains
    this.x.domain(d3.extent(this._data, function(d) { return d.datetime; }));
    this.y.domain([
        0, // -1 * d3.max(arg, function(d) { return d.totalExport; }),
        d3.max(arg, function(d) { return d.totalProduction + d.totalImport; })
    ]);
    var modeColors = this.modeOrder.map(function(d) { return that.modeColor[d]; });
    this.z
        .domain(keys)
        .range(
            modeColors.concat(exchangeKeysSet
                .values()
                .map(function(d) { return 'white' })
            ))

    return this;
}

AreaGraph.prototype.render = function() {
    // Convenience
    var that = this,
        x = this.x,
        y = this.y,
        z = this.z,
        stack = this.stack,
        data = this._data;

    if (!data || !stack) { return this; }

    // Set scale range, based on effective pixel size
    var width  = this.rootElement.node().getBoundingClientRect().width,
        height = this.rootElement.node().getBoundingClientRect().height;
    if (!width || !height) return this;
    var X_AXIS_HEIGHT = 20;
    var X_AXIS_PADDING = 4;
    var Y_AXIS_WIDTH = 35;
    var Y_AXIS_PADDING = 4;
    x.range([0, width - Y_AXIS_WIDTH]);
    y.range([height - X_AXIS_HEIGHT, Y_AXIS_PADDING]);

    this.verticalLine
        .attr('y1', 0)
        .attr('y2', height);

    var area = d3.area()
        .x(function(d, i) { return x(d.data.datetime); })
        .y0(function(d) { return y(d[0]); })
        .y1(function(d) { return y(d[1]); });

    // Create required gradients
    var linearGradientSelection = this.rootElement.selectAll('linearGradient')
        .data(this.exchangeKeysSet.values())
    linearGradientSelection.exit().remove()
    linearGradientSelection.enter()
        .append('linearGradient')
            .attr('gradientUnits', 'userSpaceOnUse')
        .merge(linearGradientSelection)
            .attr('id', function(d) { return 'areagraph-exchange-' + d })
            .attr('x1', x.range()[0])
            .attr('x2', x.range()[1])
            .each(function(k, i) {
                var selection = d3.select(this).selectAll('stop')
                    .data(data)
                var gradientData = selection
                    .enter().append('stop');
                gradientData.merge(selection)
                    .attr('offset', function(d, i) {
                        return (that.x(d.datetime) - that.x.range()[0]) /
                            (that.x.range()[1] - that.x.range()[0]) * 100.0 + '%';
                    })
                    .attr('stop-color', function(d) {
                        if (d._countryData.exchangeCo2Intensities) {
                            return that.co2color()(d._countryData.exchangeCo2Intensities[k]);
                        } else { return 'darkgray' }
                    });
            })

    var selection = this.graphElement
        .selectAll('.layer')
        .data(stack(data))
    var layer = selection.enter().append('g')
        .attr('class', 'layer');

    layer.append('path')
        .attr('class', 'area')
    layer.merge(selection).select('path.area')
        .transition()
        .style('fill', function(d) {
            if (that.modeOrder.indexOf(d.key) != -1) {
                // Regular production mode
                return z(d.key)
            } else {
                // Exchange fill
                return 'url(#areagraph-exchange-' + d.key + ')'
            }
        })
        .attr('d', area);

    this.graphElement
        .on('mouseover', function () {
            that.verticalLine.style('display', 'block');
            if (that.mouseOverHandler)
                that.mouseOverHandler.call(this);
        })
        .on('mouseout', function () {
            that.verticalLine.style('display', 'none');
            if (that.mouseOutHandler)
                that.mouseOutHandler.call(this);
        })
        .on('mousemove', function () {
            var dx = d3.event.x - this.getBoundingClientRect().left;
            var datetime = x.invert(dx);
            // Find data point closest to
            var i = d3.bisectLeft(data.map(function(d) { return d.datetime; }), datetime);
            if (datetime - data[i-1].datetime < data[i].datetime - datetime) i--;
            that.verticalLine
                .attr('x1', x(data[i].datetime))
                .attr('x2', x(data[i].datetime));
            if (that.mouseMoveHandler)
                that.mouseMoveHandler.call(this, data[i]._countryData);
        })

    // x axis
    var xAxis = d3.axisBottom(x)
        .ticks(5)
        .tickFormat(function(d) { return moment(d).format('LT'); });
    this.xAxisElement
        // Need to remove 1px in order to see the 1px line
        .style('transform', 'translate(0, ' + (height - X_AXIS_HEIGHT) + 'px)')
        .call(xAxis);

    // y axis
    var yAxis = d3.axisRight(y)
        .ticks(5);
    this.yAxisElement
        .style('transform', 'translate(' + (width - Y_AXIS_WIDTH) + 'px, 0)')
        .call(yAxis);

    return this;
}

AreaGraph.prototype.onMouseOver = function(arg) {
    if (!arg) return this.mouseOverHandler;
    else this.mouseOverHandler = arg;
    return this;
}
AreaGraph.prototype.onMouseOut = function(arg) {
    if (!arg) return this.mouseOutHandler;
    else this.mouseOutHandler = arg;
    return this;
}
AreaGraph.prototype.onMouseMove = function(arg) {
    if (!arg) return this.mouseMoveHandler;
    else this.mouseMoveHandler = arg;
    return this;
}
AreaGraph.prototype.co2color = function(arg) {
    if (!arg) return this._co2color;
    else this._co2color = arg;
    return this;
}

module.exports = AreaGraph;
