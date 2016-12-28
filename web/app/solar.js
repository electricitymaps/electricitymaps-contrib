var exports = module.exports = {};

var d3 = require('d3');
var moment = require('moment');

var grib = require('./grib');

var solarCanvas;

function bilinearInterpolate(x, y, x1, x2, y1, y2, Q11, Q12, Q21, Q22) {
    var R1 = ((x2 - x)/(x2 - x1))*Q11 + ((x - x1)/(x2 - x1))*Q21;
    var R2 = ((x2 - x)/(x2 - x1))*Q12 + ((x - x1)/(x2 - x1))*Q22;
    return ((y2 - y)/(y2 - y1))*R1 + ((y - y1)/(y2 - y1))*R2;
}

exports.draw = function(canvasSelector, now, grib1, grib2, solarColor, projection, callback) {
    // Interpolates between two solar forecasts
    var t_before = grib.getTargetTime(grib1);
    var t_after = grib.getTargetTime(grib2);
    console.log('#1 solar forecast target', 
        moment(t_before).fromNow(),
        'made', moment(grib1.header.refTime).fromNow());
    console.log('#2 solar forecast target',
        moment(t_after).fromNow(),
        'made', moment(grib2.header.refTime).fromNow());
    if (moment(now) > moment(t_after)) {
        return console.error('Error while interpolating solar because current time is out of bounds');
    }
    var k = (now - t_before)/(t_after - t_before);
    var buckets = d3.range(solarColor.range().length)
        .map(function(d) { return []; });
    var bucketIndex = d3.scaleLinear()
        .rangeRound(d3.range(buckets.length))
        .domain(solarColor.domain())
        .clamp(true);
    var k = (now - t_before)/(t_after - t_before);

    var Nx = grib1.header.nx;
    var Ny = grib1.header.ny;
    var lo1 = grib1.header.lo1;
    var la1 = grib1.header.la1;
    var dx = grib1.header.dx;
    var dy = grib1.header.dy;

    solarCanvas = d3.select(canvasSelector);

    var xrange = d3.range(solarCanvas.attr('width'));
    function batchDrawColumns(x, batchsize, callback) {
        var batch = d3.range(Math.min(batchsize, xrange[xrange.length - 1] - x))
            .map(function(d) { return d + x; });
        console.log('Drawing solar', x, '/', xrange[xrange.length - 1]);
        batch.forEach(function(x) {
            d3.range(solarCanvas.attr('height')).forEach(function(y) {
                var lonlat = projection.invert([x, y]);
                var positions = [
                    [Math.floor(lonlat[0] - lo1) / dx, Math.ceil(la1 - lonlat[1]) / dy],
                    [Math.floor(lonlat[0] - lo1) / dx, Math.floor(la1 - lonlat[1]) / dy],
                    [Math.ceil(lonlat[0] - lo1) / dx, Math.ceil(la1 - lonlat[1]) / dy],
                    [Math.ceil(lonlat[0] - lo1) / dx, Math.floor(la1 - lonlat[1]) / dy],
                ];
                var values = positions.map(function(d) {
                    var n = d[0] + Nx * d[1];
                    return d3.interpolate(
                        grib1.data[n],
                        grib2.data[n])(k);
                });
                var val = bilinearInterpolate(
                    (lonlat[0] - lo1) / dx,
                    (la1 - lonlat[1]) / dy,
                    positions[0][0],
                    positions[2][0],
                    positions[0][1],
                    positions[1][1],
                    values[0],
                    values[1],
                    values[2],
                    values[3]);
                buckets[bucketIndex(val)].push([x, y]);
            });
        });

        if (x + batchsize <= xrange[xrange.length - 1]) {
            setTimeout(function() { return batchDrawColumns(x + batchsize, batchsize, callback); }, 25);
        } else {
            console.log('Done drawing solar');
            callback(null);
        }
    }

    batchDrawColumns(0, 200, function() {
        var ctx = solarCanvas.node().getContext('2d');
        ctx.clearRect(0, 0, parseInt(solarCanvas.attr('width')), parseInt(solarCanvas.attr('height')));
        buckets.forEach(function(d, i) {
            ctx.beginPath()
            rgbaColor = solarColor.range()[i];
            ctx.strokeStyle = d3.rgb(rgbaColor.replace('rgba', 'rgb'));
            ctx.globalAlpha = parseFloat(rgbaColor
                .replace('(', '')
                .replace(')', '')
                .replace('rgba', '')
                .split(', ')[3]);
            d.forEach(function(d) { ctx.rect(d[0], d[1], 1, 1); });
            ctx.stroke();
        });
        buckets = []; // Release memory
        callback(null);
    });
};

exports.show = function() {
    solarCanvas.transition().style('opacity', 1);
}

exports.hide = function() {
    if(solarCanvas) solarCanvas.transition().style('opacity', 0);
}
