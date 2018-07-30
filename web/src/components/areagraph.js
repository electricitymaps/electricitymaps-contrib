'use strict'

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-axis'),
  require('d3-collection'),
  require('d3-selection'),
  require('d3-scale'),
  require('d3-shape'),
);
// see https://stackoverflow.com/questions/36887428/d3-event-is-null-in-a-reactjs-d3js-component
import {event as currentEvent} from 'd3-selection';
var moment = require('moment');

function AreaGraph(selector, modeColor, modeOrder) {
    var that = this;

    this.rootElement = d3.select(selector);

    // Create axis
    this.xAxisElement = this.rootElement.append('g')
        .attr('class', 'x axis')
        .style('pointer-events', 'none');
    this.yAxisElement = this.rootElement.append('g')
        .attr('class', 'y axis')
        .style('pointer-events', 'none');

    this.graphElement = this.rootElement.append('g');
    this.interactionRect = this.graphElement.append('rect')
        .style('cursor', 'pointer')
        .style('opacity', 0);
    this.verticalLine = this.rootElement.append('line')
        .attr('class', 'vertical-line')
        .style('display', 'none')
        .style('pointer-events', 'none')
        .style('shape-rendering', 'crispEdges')

    this.markerElement = this.rootElement.append('circle')
        .style('pointer-events', 'none')
        .style('display', 'none')
        .attr('r', 6)
        .style('stroke', 'black')
        .style('stroke-width', 1.5);

    // Create scales
    this.x = d3.scaleTime();
    this.y = d3.scaleLinear();
    this.z = d3.scaleOrdinal();

    this._area = d3.area()
        .x(function(d, i) { return that.x(d.data.datetime); })
        .y0(function(d) { return that.y(d[0]); })
        .y1(function(d) { return that.y(d[1]); })
        .defined(function(d, i) { return isFinite(d[1]); });

    // Other variables
    this.modeColor = modeColor;
    this.modeOrder = modeOrder;
}

AreaGraph.prototype.data = function (arg) {
    if (!arguments.length) return this._originalData;
    if (!arg) {
        return this;
    }

    // Keep the original data
    this._originalData = arg;

    var that = this;

    // Parse data
    var exchangeKeysSet = this.exchangeKeysSet = d3.set();
    this._data = arg.map(function(d) {
        var obj = {
            datetime: moment(d.stateDatetime).toDate()
        };
        // Add production
        that.modeOrder.forEach(function(k) {
            var isStorage = k.indexOf('storage') != -1
            var value = isStorage ?
                -1 * Math.min(0, (d.storage || {})[k.replace(' storage', '')]) :
                (d.production || {})[k]
            obj[k] = value;
            if (isFinite(value) && that._displayByEmissions && obj[k] != null) {
                // in tCO2eq/min
                if (isStorage && obj[k] >= 0) {
                    obj[k] *= d.dischargeCo2Intensities[k] / 1e3 / 60.0
                } else {
                    obj[k] *= d.productionCo2Intensities[k] / 1e3 / 60.0
                }
            }
        })
        // Add exchange
        d3.entries(d.exchange).forEach(function(o) {
            exchangeKeysSet.add(o.key);
            obj[o.key] = Math.max(0, o.value);
            if (isFinite(o.value) && that._displayByEmissions && obj[o.key] != null) {
                // in tCO2eq/min
                obj[o.key] *= d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
            }
        });
        // Keep a pointer to original data
        obj._countryData = d;
        return obj;
    });

    // Prepare stack
    // Order is defined here, from bottom to top
    this.stackKeys = this.modeOrder
        .concat(exchangeKeysSet.values())
    this.stack = d3.stack()
        .offset(d3.stackOffsetDiverging)
        .keys(this.stackKeys)(this._data);

    // Set domains
    if (this._xDomain) {
        this.x.domain(this._xDomain);
    } else {
        this.x.domain(d3.extent(this._data, function(d) { return d.datetime; }));
    }
    this.y.domain([
        0,
        1.1 * d3.max(arg, function(d) {
            if (!that._displayByEmissions) {
                return d.totalProduction + d.totalImport + d.totalDischarge;
            } else {
                // in tCO2eq/min
                return (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0;
            }
        })
    ]);
    this.z
        .domain(this.stackKeys)
        .range(this.stackKeys.map(function(d) { return that.modeColor[d] }))

    // Cache datetimes
    this._datetimes = this._data.map(function(d) { return d.datetime; });

    return this;
}

AreaGraph.prototype.render = function() {
    // Convenience
    var that = this,
        x = this.x,
        y = this.y,
        z = this.z,
        stack = this.stack,
        data = this._data,
        area = this._area;

    if (!data || !stack) { return this; }

    // Update scale if needed
    if (this._xDomain) {
        x.domain(this._xDomain);
    }

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
        .attr('y1', y.range()[0])
        .attr('y2', y.range()[1]);

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
        .data(stack)
    selection.exit().remove();
    var layer = selection.enter().append('path')
        .attr('class', function(d) { return 'area layer ' + d.key })


    var datetimes = this._datetimes;
    function detectPosition(d3Event) {
        if (!d3Event) { d3Event = currentEvent; }
        if (!datetimes.length) return;
        var dx = d3Event.pageX ? (d3Event.pageX - this.parentNode.getBoundingClientRect().left) :
            (d3.touches(this)[0][0]);
        var datetime = x.invert(dx);
        // Find data point closest to
        var i = d3.bisectLeft(datetimes, datetime);
        if (i > 0 && datetime - datetimes[i-1] < datetimes[i] - datetime)
            i--;
        if (i > datetimes.length - 1) i = datetimes.length - 1;
        return i;
    }

    // Warning: because the area and the background are two separate elements,
    // switching the mouse from one to the other will cause an unwanted mouseout.
    // Therefore, we should debounce the mouseout and verify no mouseover is triggered withing
    // a very small time
    var mouseOutTimeout;

    layer.merge(selection)
        .on('mousemove', function(d, j) {
            var i = detectPosition.call(this);
            that.selectedIndex(i);
            that._selectedLayerIndex = j;
            if (that.layerMouseMoveHandler) {
                that.layerMouseMoveHandler.call(this, d.key, d[i].data._countryData)
            }
            if (that.mouseMoveHandler)
                that.mouseMoveHandler.call(this, data[i]._countryData, i);
        })
        .on('mouseover', function(d, j) {
            if (mouseOutTimeout) {
                clearTimeout(mouseOutTimeout);
                mouseOutTimeout = undefined;
            }
            var i = detectPosition.call(this);
            that._selectedLayerIndex = j;
            that.selectedIndex(i);
            if (that.layerMouseOverHandler) {
                that.layerMouseOverHandler.call(this, d.key, d[i].data._countryData, i)
            }
            if (that.mouseOverHandler)
                that.mouseOverHandler.call(this, data[i]._countryData, i);
        })
        .on('mouseout', function(d) {
            var innerThis = this;
            that._selectedLayerIndex = undefined;
            that.selectedIndex(undefined);
            mouseOutTimeout = setTimeout(function() {
                if (that.mouseOutHandler)
                    that.mouseOutHandler.call(innerThis);
            }, 50)
            if (that.layerMouseOutHandler) {
                that.layerMouseOutHandler.call(innerThis, d.key)
            }
        })
        .transition()
        .style('fill', function(d) { return fillColor.call(that, d) })
        .attr('d', area);

    this.interactionRect
        .attr('x', x.range()[0])
        .attr('y', y.range()[1])
        .attr('width', x.range()[1] - x.range()[0])
        .attr('height', y.range()[0] - y.range()[1])
        .on('mouseover', function () {
            if (!data.length) { return; }
            if (mouseOutTimeout) {
                clearTimeout(mouseOutTimeout);
                mouseOutTimeout = undefined;
            }
            var i = detectPosition.call(this);
            that.selectedIndex(i);
            if (that.mouseOverHandler)
                that.mouseOverHandler.call(this, data[i]._countryData, i);
        })
        .on('mouseout', function () {
            if (!data.length) { return; }
            var innerThis = this;
            var d3Event = currentEvent;
            mouseOutTimeout = setTimeout(function() {
                var i = detectPosition.call(innerThis, d3Event);
                that.selectedIndex(i);
                if (that.mouseOutHandler)
                    that.mouseOutHandler.call(innerThis, data[i]._countryData, i);
            }, 100)
        })
        .on('mousemove', function () {
            if (!data.length) { return; }
            var i = detectPosition.call(this);
            if (that.mouseMoveHandler)
                that.mouseMoveHandler.call(this, data[i]._countryData, i);
        })

    // x axis
    var xAxis = d3.axisBottom(x)
        .ticks(5)
        .tickFormat(function(d) { return moment(d).format('LT'); });
    this.xAxisElement
        .attr('transform', `translate(-1 ${height - X_AXIS_HEIGHT - 1})`)
        .call(xAxis);

    // y axis
    var yAxis = d3.axisRight(y)
        .ticks(5);
    this.yAxisElement
        .attr('transform', `translate(${width - Y_AXIS_WIDTH - 1} -1)`)
        .call(yAxis);

    return this;
}

// ** PRIVATE **
function fillColor(d) {
    if (this.modeOrder.indexOf(d.key) != -1) {
        // Regular production mode
        return this.z(d.key)
    } else {
        // Exchange fill
        if (this._displayByEmissions) {
            return 'darkgray'
        } else {
            return 'url(#areagraph-exchange-' + d.key + ')'
        }
    }
}


// ** PUBLIC **
AreaGraph.prototype.onMouseOver = function(arg) {
    if (!arguments.length) return this.mouseOverHandler;
    else this.mouseOverHandler = arg;
    return this;
}
AreaGraph.prototype.onMouseOut = function(arg) {
    if (!arguments.length) return this.mouseOutHandler;
    else this.mouseOutHandler = arg;
    return this;
}
AreaGraph.prototype.onMouseMove = function(arg) {
    if (!arguments.length) return this.mouseMoveHandler;
    else this.mouseMoveHandler = arg;
    return this;
}
AreaGraph.prototype.onLayerMouseOver = function(arg) {
    if (!arguments.length) return this.layerMouseOverHandler;
    else this.layerMouseOverHandler = arg;
    return this;
}
AreaGraph.prototype.onLayerMouseOut = function(arg) {
    if (!arguments.length) return this.layerMouseOutHandler;
    else this.layerMouseOutHandler = arg;
    return this;
}
AreaGraph.prototype.onLayerMouseMove = function(arg) {
    if (!arguments.length) return this.layerMouseMoveHandler;
    else this.layerMouseMoveHandler = arg;
    return this;
}
AreaGraph.prototype.co2color = function(arg) {
    if (!arguments.length) return this._co2color;
    else this._co2color = arg;
    return this;
}
AreaGraph.prototype.xDomain = function(arg) {
    if (!arguments.length) return this._xDomain;
    else this._xDomain = arg;
    return this;
}
AreaGraph.prototype.selectedIndex = function(arg) {
    if (!arguments.length) return this._selectedIndex;
    else {
        var that = this;

        this._selectedIndex = arg;
        if (!this._data) { return this; }
        if (this._selectedIndex == null) {
            this.verticalLine.style('display', 'none')    
        } else {
            this.verticalLine
                .attr('x1', this.x(this._data[this._selectedIndex].datetime))
                .attr('x2', this.x(this._data[this._selectedIndex].datetime))
                .style('display', 'block');
        }
        if (this._selectedLayerIndex != null && this._selectedIndex != null) {
            var selectedData = this.stack[this._selectedLayerIndex][this._selectedIndex];
            this.markerElement
                .attr('cx', this.x(this._data[this._selectedIndex].datetime))
                .attr('cy', this.y(selectedData[1]))
                .style('display', 'block')
                .style('fill', function() {
                    return fillColor.call(that, {
                        key: that.stackKeys[that._selectedLayerIndex]
                    })
                })
        } else {
            this.markerElement.style('display', 'none')
        }
    }
    return this;
}
AreaGraph.prototype.displayByEmissions = function(arg) {
    if (arg === undefined) return this._displayByEmissions;
    else {
        this._displayByEmissions = arg;
        // Quick hack to re-render
        // TODO: In principle we shouldn't be calling `.data()`
        this
            .data(this._originalData)
            .render();
    }
    return this;
}

module.exports = AreaGraph;
