var exports = module.exports = {};

var d3 = require('d3');
var moment = require('moment');

var grib = require('../../helpers/grib');
var Windy = require('../../helpers/windy');

var windCanvas;
var projection;
var windLayer;

var lastDraw;
var hidden = true;

var WIND_OPACITY = 0.53;

exports.isExpired = function(now, grib1, grib2) {
    return grib.getTargetTime(grib2[0]) <= moment(now) || grib.getTargetTime(grib1[0]) > moment(now);
}

exports.draw = function(canvasSelector, now, gribs1, gribs2, windColor, argProjection) {
    if (!argProjection)
        throw Error('Projection can\'t be null/undefined');

    // Only redraw after 5min
    if (lastDraw && (lastDraw - new Date().getTime()) < 1000 * 60 * 5) {
        return;
    }

    lastDraw = new Date().getTime();

    var t_before = grib.getTargetTime(gribs1[0]);
    var t_after = grib.getTargetTime(gribs2[0]);
    console.log('#1 wind forecast target', 
        t_before.fromNow(),
        'made', grib.getRefTime(gribs1[0]).fromNow());
    console.log('#2 wind forecast target', 
        t_after.fromNow(),
        'made', grib.getRefTime(gribs2[0]).fromNow());
    // Interpolate wind
    var interpolatedWind = gribs1;
    if (moment(now) > t_after) {
        console.error('Error while interpolating wind because current time is out of bounds');
    } else {
        var k = (now - t_before)/(t_after - t_before);
        interpolatedWind[0].data = interpolatedWind[0].data.map(function (d, i) {
            return d3.interpolate(d, gribs2[0].data[i])(k)
        });
        interpolatedWind[1].data = interpolatedWind[1].data.map(function (d, i) {
            return d3.interpolate(d, gribs2[1].data[i])(k)
        });
        windCanvas = d3.select(canvasSelector);
        projection = argProjection;
        if (!windLayer) windLayer = new Windy({ canvas: windCanvas.node(), projection: projection });
        windLayer.params.data = interpolatedWind;
    }
};

exports.zoomend = function() {
    // Called when the dragging / zooming is done.
    // We need to re-update change the projection
    if (!projection || !windLayer || hidden) { return; }

    var width = parseInt(windCanvas.node().parentNode.getBoundingClientRect().width);
    var height = parseInt(windCanvas.node().parentNode.getBoundingClientRect().height);

    var sw = projection.invert([0, height]);
    var ne = projection.invert([width, 0]);

    windLayer.start( // Note: this blocks UI..
        [[0, 0], [width, height]], 
        width,
        height,
        [sw, ne]
    );
}

exports.pause = function(arg) {
    if (windLayer)
        windLayer.paused = arg;
}

exports.show = function() {
    if (!windCanvas) { return; }
    if (windLayer && windLayer.started) { return; }
    var width = parseInt(windCanvas.node().parentNode.getBoundingClientRect().width);
    var height = parseInt(windCanvas.node().parentNode.getBoundingClientRect().height);
    // Canvas needs to have it's width and height attribute set
    windCanvas
        .attr('width', width)
        .attr('height', height);

    var sw = projection.invert([0, height]);
    var ne = projection.invert([width, 0]);
    windCanvas.transition().style('opacity', WIND_OPACITY);
    windLayer.start(
        [[0, 0], [width, height]], 
        width,
        height,
        [sw, ne]
    );
    hidden = false;
};

exports.hide = function() { 
    if (windCanvas) windCanvas.transition().style('opacity', 0);
    if (windLayer) windLayer.stop();
    hidden = true;
};
