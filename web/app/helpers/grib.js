var exports = module.exports = {};

const d3 = require('d3-interpolate');
const moment = require('moment');

const getRefTime = exports.getRefTime = grib =>
  moment(grib.header.refTime);
const getTargetTime = exports.getTargetTime = grib =>
  moment(getRefTime(grib)).add(grib.header.forecastTime, 'hour');

exports.getInterpolatedValueAtLonLat = function getInterpolatedValueAtLonLat(lonlat, now, grib1, grib2) {
  const t_before = getTargetTime(grib1).toDate().getTime();
  const t_after = getTargetTime(grib2).toDate().getTime();
  now = moment(now).toDate().getTime();
  if (now > t_after || now < t_before) {
    return console.error('Can\'t interpolate value when now is outside of bounds.');
  }
  const k = (now - t_before)/(t_after - t_before);
  return d3.interpolate(
    exports.getValueAtLonLat(lonlat, grib1),
    exports.getValueAtLonLat(lonlat, grib2)
  )(k);
};
exports.getValueAtLonLat = (lonlat, grib) => {
  const Nx = grib.header.nx;
  const Ny = grib.header.ny;
  const lo1 = grib.header.lo1;
  const la1 = grib.header.la1;
  const dx = grib.header.dx;
  const dy = grib.header.dy;
  const i = parseInt(lonlat[0] - lo1) / dx;
  const j = parseInt(la1 - lonlat[1]) / dy;
  const n = j * Nx + i;
  return grib.data[n];
};
