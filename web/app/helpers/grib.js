var exports = module.exports = {};

var d3 = require('d3');
var moment = require('moment');

var getRefTime = exports.getRefTime = function(grib) {
    return moment(grib.header.refTime);
}
var getTargetTime = exports.getTargetTime = function(grib) {
    return moment(getRefTime(grib)).add(
        grib.header.forecastTime, 'hour');
}
exports.getInterpolatedValueAtLonLat = function getInterpolatedValueAtLonLat(lonlat, now, grib1, grib2) {
    var t_before = getTargetTime(grib1).toDate().getTime();
    var t_after = getTargetTime(grib2).toDate().getTime();
    now = moment(now).toDate().getTime();
    if (now > t_after || now < t_before)
        return console.error('Can\'t interpolate value when now is outside of bounds.');
    var k = (now - t_before)/(t_after - t_before);
    return d3.interpolate(
        exports.getValueAtLonLat(lonlat, grib1),
        exports.getValueAtLonLat(lonlat, grib2))(k);
}
exports.getValueAtLonLat = function getValueAtLonLat(lonlat, grib) {
    var Nx = grib.header.nx;
    var Ny = grib.header.ny;
    var lo1 = grib.header.lo1;
    var la1 = grib.header.la1;
    var dx = grib.header.dx;
    var dy = grib.header.dy;
    var i = parseInt(lonlat[0] - lo1) / dx;
    var j = parseInt(la1 - lonlat[1]) / dy;
    var n = j * Nx + i;
    return grib.data[n];
}
