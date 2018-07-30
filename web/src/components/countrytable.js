import NoDataOverlay from '../components/nodataoverlay'

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-axis'),
  require('d3-collection'),
  require('d3-format'),
  require('d3-selection'),
  require('d3-scale'),
);
var getSymbolFromCurrency = require('currency-symbol-map');
var moment = require('moment');

var flags = require('../helpers/flags');
var translation = require('../helpers/translation');

// TODO:
// All non-path (i.e. non-axis) elements should be drawn
// with a % scale.
// This means drawing them once at `.data()` or at construction, and not
// during `render()`

function CountryTable(selector, modeColor, modeOrder) {
    var that = this;

    this.root = d3.select(selector);

    this.wrapperNoDataOverlay = new NoDataOverlay('.country-panel-wrap');
    this.container = this.root.append('svg').attr('class', 'country-table');
    
    // Create containers
    this.headerRoot = this.container.append('g');
    this.productionRoot = this.container.append('g');
    this.exchangeRoot = this.container.append('g');

    // Constants
    this.ROW_HEIGHT = 13; // Height of the rects
    this.RECT_OPACITY = 0.8;
    this.LABEL_MAX_WIDTH = 102;
    this.PADDING_X = 5; this.PADDING_Y = 7; // Inner paddings
    this.FLAG_SIZE = 16;
    this.TEXT_ADJUST_Y = 11; // To align properly on a line
    this.X_AXIS_HEIGHT = 15;
    this.MODE_COLORS = modeColor;
    this.MODES = [];
    modeOrder.forEach(function(k) {
        that.MODES.push({'mode': k, 'isStorage': k.indexOf('storage') != -1});
    });
    this.SCALE_TICKS = 4;
    this.TRANSITION_DURATION = 250;

    // State
    this._displayByEmissions = false;

    // Header
    this.gPowerAxis = this.headerRoot.append('g')
        .attr('class', 'x axis');

    // Scales
    this.powerScale = d3.scaleLinear();
    this.co2Scale = d3.scaleLinear();

    // Initial objects
    // ** Production labels and rects **
    var gNewRow = this.productionRoot.selectAll('.row')
        .data(this.MODES)
        .enter()
        .append('g')
            .attr('class', 'row')
            .attr('transform', function(d, i) {
                return 'translate(0,' + (i * (that.ROW_HEIGHT + that.PADDING_Y)) + ')';
            });
    gNewRow.append('text')
        .text(function(d) { return translation.translate(d.mode) || d.mode })
        .style('text-anchor', 'end') // right align
        .attr('transform', 'translate(' + (this.LABEL_MAX_WIDTH - 1.5 * this.PADDING_Y) + ', ' + this.TEXT_ADJUST_Y + ')');
    gNewRow.append('rect')
        .attr('class', 'capacity')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill-opacity', 0.4)
        .attr('opacity', 0.3)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('rect')
        .attr('class', 'production')
        .attr('height', this.ROW_HEIGHT)
        .attr('opacity', this.RECT_OPACITY)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('text')
        .attr('class', 'unknown')
        .text('?')
        .style('fill', 'darkgray')
        .attr('transform', 'translate(1, ' + this.TEXT_ADJUST_Y + ')')
        .style('display', 'none');
    
}

CountryTable.prototype.render = function(ignoreTransitions) {
    var that = this;

    if (this.root.node().getBoundingClientRect.width === 0){
        return;
    }

    if (!this._data) {
        return;
    }
 
    // Set header
    const panel = d3.select('.left-panel-zone-details');
    const datetime = this._data.stateDatetime || this._data.datetime;
    panel.select('#country-flag').attr('src', flags.flagUri(this._data.countryCode, 24));
    panel.select('.country-name').text(
        translation.getFullZoneName(this._data.countryCode));

    panel.selectAll('.country-time')
        .text(datetime ? moment(datetime).format('LL LT') : '');
        
    if (this.isMissingParser){
        return;
    }

    const width = this.root.node().getBoundingClientRect().width;
    
    if (!this._exchangeData) { return; }

    
    // Update scale
    this.barMaxWidth = width - this.LABEL_MAX_WIDTH - this.PADDING_X;
    this.powerScale
        .range([0, this.barMaxWidth]);
    this.co2Scale
        .range([0, this.barMaxWidth]);

    var axisHeight = 
        (this.MODES.length + this._exchangeData.length + 1) * (this.ROW_HEIGHT + this.PADDING_Y)
        + this.PADDING_Y;

    this.axis
        .tickSizeInner(-1 * axisHeight)
        .tickSizeOuter(0)
        .ticks(this.SCALE_TICKS);

    this.gPowerAxis
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        // TODO: We should offset by just one pixel because it looks better when
        // the rectangles don't start exactly on the axis...
        // But we should also handle "negative" rects
        .attr('transform', 'translate(' + (this.powerScale.range()[0] + this.LABEL_MAX_WIDTH) + ', ' + this.X_AXIS_HEIGHT +')')
        .call(this.axis);


    var selection = this.productionRoot.selectAll('.row')
        .data(this.sortedProductionData);
    /*selection.select('rect.capacity')
        .attr('fill', function (d) { return that.co2color()(d.gCo2eqPerkWh); })
        .attr('stroke', function (d) { return that.co2color()(d.gCo2eqPerkWh); });*/

    if (that._displayByEmissions)
        selection.select('rect.capacity')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .style('display', 'none')
    else
        selection.select('rect.capacity')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('x', function(d) {
                var value = (!d.isStorage) ? d.capacity : -1 * d.capacity;
                return that.LABEL_MAX_WIDTH + ((value == undefined || !isFinite(value)) ? that.powerScale(0) : that.powerScale(Math.min(0, value)));
            })
            .attr('width', function (d) {
                var isDefined = d.capacity !== undefined && d.capacity >= (d.production || 0);
                var capacity = d.isStorage ? (d.capacity * 2) : d.capacity
                return isDefined ? (that.powerScale(capacity) - that.powerScale(0)) : 0;
            })
            .on('end', function () { d3.select(this).style('display', 'block'); });
    // Add event handlers
    selection.selectAll('rect.capacity,rect.production')
        .on('mouseover', function (d) {
            if (that.productionMouseOverHandler)
                that.productionMouseOverHandler.call(this, d.mode, that._data, that._displayByEmissions);
        })
        .on('mouseout', function (d) {
            if (that.productionMouseOutHandler)
                that.productionMouseOutHandler.call(this, d.mode, that._data, that._displayByEmissions);
        })
        .on('mousemove', function (d) {
            if (that.productionMouseMoveHandler)
                that.productionMouseMoveHandler.call(this, d.mode, that._data, that._displayByEmissions);
        });
    /*selection.select('rect.production')
        .attr('fill', function (d) { return that.co2color()(d.gCo2eqPerkWh); });*/
    if (that._displayByEmissions)
        selection.select('rect.production')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('fill', function (d) {
                // color by Co2 Intensity
                // return that.co2color()(that._data.productionCo2Intensities[d.mode, that._data.countryCode]);
                // color by production mode
                return that.MODE_COLORS[d.mode];
            })
            .attr('x', that.LABEL_MAX_WIDTH + that.co2Scale(0))
            .attr('width', function (d) {
                return !isFinite(d.gCo2eqPerH) ? 0 : (that.co2Scale(d.gCo2eqPerH / 1e6 / 60.0) - that.co2Scale(0));
            });
    else
        selection.select('rect.production')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('fill', function (d) {
                return that.MODE_COLORS[d.mode];
            })
            .attr('x', function (d) {
                var value = (!d.isStorage) ? d.production : -1 * d.storage;
                return that.LABEL_MAX_WIDTH + ((value == undefined || !isFinite(value)) ? that.powerScale(0) : that.powerScale(Math.min(0, value)));
            })
            .attr('width', function (d) {
                var value = d.production != undefined ? d.production : -1 * d.storage;
                return (value == undefined || !isFinite(value)) ? 0 : Math.abs(that.powerScale(value) - that.powerScale(0));
            });
    selection.select('text.unknown')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .attr('x', that.LABEL_MAX_WIDTH + (that._displayByEmissions ? that.co2Scale(0) : that.powerScale(0)))
        .style('display', function (d) {
            return (d.capacity == undefined || d.capacity > 0) && 
                d.mode != 'unknown' && 
                (d.isStorage ? d.storage == undefined : d.production == undefined) ?
                'block' : 'none';
        });

    // Construct exchanges
    function getExchangeCo2eq(d) {
        return d.value > 0 ? 
            (that._data.exchangeCo2Intensities !== undefined && that._data.exchangeCo2Intensities[d.key] !== undefined) ? that._data.exchangeCo2Intensities[d.key] : undefined
            : (that._data.co2intensity !== undefined) ? that._data.co2intensity : undefined;
    }
    var selection = this.exchangeRoot.selectAll('.row')
        .data(this._exchangeData);
    selection.exit().remove();

    var gNewRow = selection.enter().append('g')
        .attr('class', 'row')
        .attr('transform', function (d, i) {
            return 'translate(0,' + i * (that.ROW_HEIGHT + that.PADDING_Y) + ')';
        });
    gNewRow.append('image')
        .attr('width', this.FLAG_SIZE)
        .attr('height', this.FLAG_SIZE);
    gNewRow.append('text')
        .style('text-anchor', 'end') // right align
        .attr('transform', 
            'translate(' + (this.LABEL_MAX_WIDTH - 2.0 * this.PADDING_X) + ', ' +
                this.TEXT_ADJUST_Y + ')');
    gNewRow.append('text')
        .attr('class', 'unknown')
        .style('fill', 'darkgray')
        .text('?');
    gNewRow.append('rect')
        .attr('class', 'capacity')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill-opacity', 0.4)
        .attr('opacity', 0.3)
        .attr('shape-rendering', 'crispEdges')
        .attr('x', that.LABEL_MAX_WIDTH + 
            (this._displayByEmissions ? this.co2Scale(0) : this.powerScale(0)))
        .style('transform-origin', 'left');
    gNewRow.append('rect')
        .attr('class', 'exchange')
        .attr('height', this.ROW_HEIGHT)
        .attr('opacity', this.RECT_OPACITY)
        .attr('x', that.LABEL_MAX_WIDTH + 
            (this._displayByEmissions ? this.co2Scale(0) : this.powerScale(0)))
        .style('transform-origin', 'left');


    if (that._displayByEmissions)
        gNewRow.merge(selection).select('rect.capacity')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .style('display', 'none')
    else
        gNewRow.merge(selection).select('rect.capacity')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('x', function(d) {
                var value = ((that._data.exchangeCapacities || {})[d.key] || [undefined, undefined])[0];
                return that.LABEL_MAX_WIDTH + ((value == undefined || !isFinite(value)) ? that.powerScale(0) : that.powerScale(Math.min(0, value)));
            })
            .attr('width', function (d) {
                var capacity = (that._data.exchangeCapacities || {})[d.key];
                if (!capacity) return 0;
                return that.powerScale(capacity[1] - capacity[0]) - that.powerScale(0);
            })
            .on('end', function () { d3.select(this).style('display', 'block'); });

    gNewRow.merge(selection).select('text.unknown')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .attr('transform', 'translate(' + (that.LABEL_MAX_WIDTH + that.co2Scale(0)) + ', ' + this.TEXT_ADJUST_Y + ')')
        .style('display', function(d) {
            return (that._displayByEmissions && getExchangeCo2eq(d) === undefined) ? 'block' : 'none';
        });
    var labelLength = d3.max(this._exchangeData, function(d) { return d.key.length }) * 8;
    gNewRow.merge(selection).select('image')
        .attr('x', this.LABEL_MAX_WIDTH - 4.0 * this.PADDING_X - this.FLAG_SIZE - labelLength)
        .attr('xlink:href', function (d) {
            return flags.flagUri(d.key, that.FLAG_SIZE);
        })
    gNewRow.merge(selection).select('rect.exchange')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .attr('fill', function (d, i) {
            if (that._displayByEmissions)
                return 'gray';
            else {
                var co2intensity = getExchangeCo2eq(d);
                return (co2intensity !== undefined) ? that.co2color()(co2intensity) : 'gray';
            }
        })
        .attr('x', function (d) {
            if (that._displayByEmissions) {
                var co2intensity = getExchangeCo2eq(d);
                if (getExchangeCo2eq(d) === undefined)
                    return that.LABEL_MAX_WIDTH;
                else
                    return that.LABEL_MAX_WIDTH + that.co2Scale(Math.min((d.value || 0.0) / 1e3 / 60.0 * co2intensity, 0));
            }
            else {
                return that.LABEL_MAX_WIDTH + that.powerScale(Math.min(d.value || 0.0, 0.0));
            }
        })
        .attr('width', function (d) { 
            if (that._displayByEmissions) {
                var co2intensity = getExchangeCo2eq(d);
                if (getExchangeCo2eq(d) === undefined)
                    return 0;
                else
                    return Math.abs(that.co2Scale((d.value || 0.0) / 1e3 / 60.0 * co2intensity) - that.co2Scale(0));
            }
            else
                return Math.abs(that.powerScale(d.value || 0.0) - that.powerScale(0));
        })

    // Add event handlers
    gNewRow.merge(selection).selectAll('rect.capacity,rect.exchange')
        .on('mouseover', function (d) {
            if (that.exchangeMouseOverHandler)
                that.exchangeMouseOverHandler.call(this, d.key, that._data, that._displayByEmissions);
        })
        .on('mouseout', function (d) {
            if (that.exchangeMouseOutHandler)
                that.exchangeMouseOutHandler.call(this, d.key, that._data, that._displayByEmissions);
        })
        .on('mousemove', function (d) {
            if (that.exchangeMouseMoveHandler)
                that.exchangeMouseMoveHandler.call(this, d.key, that._data, that._displayByEmissions);
        });

    gNewRow.merge(selection).select('text')
        .text(function(d) { return d.key; });
    d3.select('.country-emission-intensity')
        .text(Math.round(this._data.co2intensity) || '?');
    var hasFossilFuelData = this._data.fossilFuelRatio != null;
    var fossilFuelPercent = this._data.fossilFuelRatio * 100;
    d3.selectAll('.left-panel-zone-details .lowcarbon-percentage')
        .text(hasFossilFuelData ? Math.round(100 - fossilFuelPercent) : '?');

    var hasRenewableData = this._data.renewableRatio != null;
    var renewablePercent = this._data.renewableRatio * 100;
    d3.selectAll('.left-panel-zone-details .renewable-percentage')
        .text(hasRenewableData ? Math.round(renewablePercent) : '?');

    var priceData = this._data.price || {};
    var hasPrice = priceData.value != null;
    d3.select('.country-spot-price')
        .text(hasPrice ? Math.round(priceData.value) : '?')
        .style('color', (priceData.value || 0) < 0 ? 'red' : undefined);
    d3.select('.country-spot-price-currency')
        .text(getSymbolFromCurrency(priceData.currency) || priceData.currency || '?')
    d3.select('#country-emission-rect, .left-panel-zone-details .emission-rect')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .style('background-color',
            this._data.co2intensity ?
                that.co2color()(this._data.co2intensity) : 'gray');
    d3.select('.country-data-source')
        .text(this._data.source || '?');

    this.resize();

    return this;
}

CountryTable.prototype.displayByEmissions = function(arg) {
    if (arg === undefined) return this._displayByEmissions;
    else {
        this._displayByEmissions = arg;
        // Quick hack to re-render
        // TODO: In principle we shouldn't be calling `.data()`
        if (this._data){
            this
            .data(this._data)
            .render();
        }

    }
    return this;
}

CountryTable.prototype.onExchangeMouseOver = function(arg) {
    if (!arguments.length) return this.exchangeMouseOverHandler;
    else this.exchangeMouseOverHandler = arg;
    return this;
}
CountryTable.prototype.onExchangeMouseOut = function(arg) {
    if (!arguments.length) return this.exchangeMouseOutHandler;
    else this.exchangeMouseOutHandler = arg;
    return this;
}
CountryTable.prototype.onExchangeMouseMove = function(arg) {
    if (!arguments.length) return this.exchangeMouseMoveHandler;
    else this.exchangeMouseMoveHandler = arg;
    return this;
}
CountryTable.prototype.onProductionMouseOver = function(arg) {
    if (!arguments.length) return this.productionMouseOverHandler;
    else this.productionMouseOverHandler = arg;
    return this;
}
CountryTable.prototype.onProductionMouseOut = function(arg) {
    if (!arguments.length) return this.productionMouseOutHandler;
    else this.productionMouseOutHandler = arg;
    return this;
}
CountryTable.prototype.onProductionMouseMove = function(arg) {
    if (!arguments.length) return this.productionMouseMoveHandler;
    else this.productionMouseMoveHandler = arg;
    return this;
}

CountryTable.prototype.resize = function() {
    this.productionHeight = this.MODES.length * (this.ROW_HEIGHT + this.PADDING_Y);
    this.exchangeHeight = (!this._data) ? 0 : d3.entries(this._exchangeData).length * (this.ROW_HEIGHT + this.PADDING_Y);

    this.yProduction = this.X_AXIS_HEIGHT + this.PADDING_Y;
    this.productionRoot
        .attr('transform', 'translate(0,' + this.yProduction + ')');
    this.yExchange = this.yProduction + this.productionHeight + this.ROW_HEIGHT + this.PADDING_Y;
    this.exchangeRoot
        .attr('transform', 'translate(0,' + this.yExchange + ')');

    this.container
        .attr('height', this.yExchange + this.exchangeHeight);
}

CountryTable.prototype.data = function(arg) {
    var that = this;
    if (!arguments.length) return this._data;

    this._data = arg;

    if (!this._data) { return this }

    this.hasProductionData = this._data.production !== undefined && Object.keys(this._data.production).length > 0;
    this.isMissingParser = this._data.hasParser === undefined || !this._data.hasParser;
    
    if (this._exchangeKeys) {
        this._exchangeData = this._exchangeKeys
            .map(function(k) {
                return { key: k, value: (that._data.exchange || {})[k] }
            })
            .sort(function(x, y) {
                return d3.ascending(x.key, y.key);
            });
    } else {
        this._exchangeData = d3.entries(this._data.exchange)
            .sort(function(x, y) {
                return d3.ascending(x.key, y.key);
            });
    }
    if (!this.hasProductionData){
        // Remove exchange data values if no production is present, as table is greyed out
        this._exchangeData.forEach(d => d.value = undefined);
    }

    // Construct a list having each production in the same order as this.MODES.
    this.sortedProductionData = this.MODES.map(function (d) {
        var footprint = !d.isStorage ? 
            that._data.productionCo2Intensities ? 
                that._data.productionCo2Intensities[d.mode] :
                undefined :
            0;
        var production = !d.isStorage ? (that._data.production || {})[d.mode] : undefined;
        var storage = d.isStorage ? (that._data.storage || {})[d.mode.replace(' storage', '')] : undefined;
        var capacity = (that._data.capacity || {})[d.mode];
        return {
            production: production,
            storage: storage,
            isStorage: d.isStorage,
            capacity: capacity,
            mode: d.mode,
            text: translation.translate(d.mode),
            gCo2eqPerkWh: footprint,
            gCo2eqPerH: footprint * 1000.0 * Math.max(production, 0)
        };
    });

    
    // update scales
    this.powerScale
        .domain(this._powerScaleDomain || [
            Math.min(
                -this._data.maxStorageCapacity || 0,
                -this._data.maxStorage || 0,
                -this._data.maxExport || 0,
                -this._data.maxExportCapacity || 0),
            Math.max(
                this._data.maxCapacity || 0,
                this._data.maxProduction || 0,
                this._data.maxDischarge || 0,
                this._data.maxStorageCapacity || 0,
                this._data.maxImport || 0,
                this._data.maxImportCapacity || 0)
        ]);
    // co2 scale in tCO2eq/min
    var maxCO2eqExport = d3.max(this._exchangeData, function (d) {
        return d.value >= 0 ? 0 : (that._data.co2intensity / 1e3 * -d.value / 60.0 || 0);
    });
    var maxCO2eqImport = d3.max(this._exchangeData, function (d) {
        if (!that._data.exchangeCo2Intensities) return 0;
        return d.value <= 0 ? 0 : that._data.exchangeCo2Intensities[d.key] / 1e3 * d.value / 60.0;
    });
    this.co2Scale // in tCO2eq/min
        .domain(this._co2ScaleDomain || [
            -maxCO2eqExport || 0,
            Math.max(
                d3.max(this.sortedProductionData, function (d) { return d.gCo2eqPerH / 1e6 / 60.0; }) || 0,
                maxCO2eqImport || 0
            )
        ]);

    // Prepare axis
    if (that._displayByEmissions) {
        var maxAxisValue = d3.max(this.co2Scale.domain());
        var p = d3.precisionPrefix(
            (d3.max(this.co2Scale.domain()) - d3.min(this.co2Scale.domain())) / (this.SCALE_TICKS - 1),
            maxAxisValue);
        var f = d3.formatPrefix('.' + p, maxAxisValue);
        this.axis = d3.axisTop(this.co2Scale)
            .tickFormat(function (d) { 
                // convert to kgs if max value is below 1t
                return maxAxisValue <= 1 ? `${d*1000} kg/min` : `${f(d)} t/min`
                })
    }
    else {
        var value = d3.max(this.powerScale.domain()) * 1e6;
        var p = d3.precisionPrefix(
            (d3.max(this.powerScale.domain()) - d3.min(this.powerScale.domain())) / (this.SCALE_TICKS - 1) * 1e6,
            value);
        var f = d3.formatPrefix('.' + p, value);
        this.axis = d3.axisTop(this.powerScale)
            .tickFormat(function (d) { return f(d * 1e6) + 'W'; });
    }

    return this;
};

// Hack to fix the scale at a minimum value
CountryTable.prototype.powerScaleDomain = function(arg) {
    if (!arguments.length) return this._powerScaleDomain;
    this._powerScaleDomain = arg;
    return this;
}
CountryTable.prototype.co2ScaleDomain = function(arg) {
    if (!arguments.length) return this._co2ScaleDomain;
    this._co2ScaleDomain = arg;
    return this;
}

CountryTable.prototype.co2color = function(arg) {
    if (!arguments.length) return this._co2color;
    else this._co2color = arg;
    return this;
};

CountryTable.prototype.exchangeKeys = function(arg) {
    if (!arguments.length) return this._exchangeKeys;
    else {
        this._exchangeKeys = arg;
        // HACK: Trigger a new data update
        this.data(this._data);
    }
    return this;
};

CountryTable.prototype.showNoParserMessageIf = function(condition) {
  const allChildrenSelector = 'p,.country-table-header-inner,.country-show-emissions-wrap,.country-panel-wrap,.country-history';
    d3.selectAll(allChildrenSelector).classed('all-screens-hidden', condition);
    d3.select('.zone-details-no-parser-message').classed('visible', condition);
}

CountryTable.prototype.showNoDataMessageIf = function(condition, isRealtimeData) {
    this.wrapperNoDataOverlay.showIfElseHide(condition);
    this.wrapperNoDataOverlay.text(translation.translate(isRealtimeData? 'country-panel.noLiveData' : 'country-panel.noDataAtTimestamp'));
}

module.exports = CountryTable;
