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

exports.isExpired = function(now, grib1, grib2) {
    return grib.getTargetTime(grib2) <= moment(now) || grib.getTargetTime(grib1) > moment(now);
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

    var alphas = solarColor.range().map(function(d) {
        return parseFloat(d
            .replace('(', '')
            .replace(')', '')
            .replace('rgba', '')
            .split(', ')[3])
    });

    solarCanvas = d3.select(canvasSelector);
    var ctx = solarCanvas.node().getContext('2d');
        realW = solarCanvas.node().getBoundingClientRect().width,
        realH = solarCanvas.node().getBoundingClientRect().height;
    var w = realW,
        h = realH;
    var scaleX = realW / w,
        scaleY = realH / h;
    function canvasInvertedProjection(arr) {
        return projection.invert([arr[0] * scaleX, arr[1] * scaleY]);
    }

    var img = ctx.createImageData(w, h);

    var xrange = d3.range(w);
    function batchDrawColumns(x, batchsize, callback) {
        var batch = d3.range(Math.min(batchsize, xrange[xrange.length - 1] - x))
            .map(function(d) { return d + x; });
        console.log('Drawing solar', x, '/', xrange[xrange.length - 1]);
        batch.forEach(function(x) {
            d3.range(h).forEach(function(y) {
                var lonlat = canvasInvertedProjection([x, y]);
                var positions = [
                    [Math.floor(lonlat[0] - lo1) / dx, Math.floor(la1 - lonlat[1]) / dy + 1],
                    [Math.floor(lonlat[0] - lo1) / dx, Math.floor(la1 - lonlat[1]) / dy],
                    [Math.floor(lonlat[0] - lo1) / dx + 1, Math.floor(la1 - lonlat[1]) / dy + 1],
                    [Math.floor(lonlat[0] - lo1) / dx + 1, Math.floor(la1 - lonlat[1]) / dy],
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
                img.data[((y*(img.width*4)) + (x*4)) + 3] = parseInt(alphas[bucketIndex(val)] * 255);
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
        ctx.clearRect(0, 0, w, h);
        ctx.putImageData(img, 0, 0);
        callback(null);
    });
};

exports.show = function() {
    solarCanvas.transition().style('opacity', 1);
}

exports.hide = function() {
    if(solarCanvas) solarCanvas.transition().style('opacity', 0);
}
