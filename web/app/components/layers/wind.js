const exports = module.exports = {};

const d3 = Object.assign(
  {},
  require('d3-interpolate'),
  require('d3-selection'),
);

const moment = require('moment');

const grib = require('../../helpers/grib');
const Windy = require('../../helpers/windy');

const WIND_OPACITY = 0.53;

let windCanvas;
let windLayer;
let lastDraw;
let hidden = true;

exports.isExpired = (now, grib1, grib2) =>
  grib.getTargetTime(grib2[0]) <= moment(now) ||
    grib.getTargetTime(grib1[0]) > moment(now);

exports.draw = (canvasSelectorId, now, gribs1, gribs2, windColor, project, unproject) => {
  if (!project) {
    throw Error('Projection can\'t be null/undefined');
  }
  if (!unproject) {
    throw Error('Unprojection can\'t be null/undefined');
  }

  // Only redraw after 5min
  if (lastDraw && (lastDraw - new Date().getTime()) < 1000 * 60 * 5) {
    return;
  }

  lastDraw = new Date().getTime();

  const t_before = grib.getTargetTime(gribs1[0]);
  const t_after = grib.getTargetTime(gribs2[0]);
  console.log(
    '#1 wind forecast target',
    t_before.fromNow(),
    'made', grib.getRefTime(gribs1[0]).fromNow(),
  );
  console.log(
    '#2 wind forecast target',
    t_after.fromNow(),
    'made', grib.getRefTime(gribs2[0]).fromNow(),
  );
  // Interpolate wind
  const interpolatedWind = gribs1;
  if (moment(now) > t_after) {
    console.error('Error while interpolating wind because current time is out of bounds');
  } else {
    const k = (now - t_before) / (t_after - t_before);
    interpolatedWind[0].data = interpolatedWind[0].data.map((d, i) =>
      d3.interpolate(d, gribs2[0].data[i])(k));
    interpolatedWind[1].data = interpolatedWind[1].data.map((d, i) =>
      d3.interpolate(d, gribs2[1].data[i])(k));
    windCanvas = document.getElementById(canvasSelectorId);
    // Only recreate if not already created
    if (!windLayer) {
      windLayer = new Windy({
        canvas: windCanvas,
        project: project,
        unproject: unproject,
      });
    }
    windLayer.params.data = interpolatedWind;
  }
};

exports.zoomend = () => {
  // Called when the dragging / zooming is done.
  // We need to re-update change the projection
  if (!windLayer || hidden) { return; }

  const width = parseInt(windCanvas.parentNode.getBoundingClientRect().width, 10);
  const height = parseInt(windCanvas.parentNode.getBoundingClientRect().height, 10);

  let unproject = windLayer.params.unproject;

  const sw = unproject([0, height]);
  const ne = unproject([width, 0]);

  // Note: the only reason we restart here is to
  // set sw and ne.
  windLayer.start( // Note: this blocks UI..
    [[0, 0], [width, height]],
    width,
    height,
    [sw, ne],
  );
};

exports.pause = (arg) => {
  if (windLayer) {
    windLayer.paused = arg;
  }
};

exports.show = () => {
  if (!windCanvas) { return; }
  if (windLayer && windLayer.started) { return; }
  const width = parseInt(windCanvas.parentNode.getBoundingClientRect().width, 10);
  const height = parseInt(windCanvas.parentNode.getBoundingClientRect().height, 10);
  // Canvas needs to have it's width and height attribute set
  windCanvas.width = width;
  windCanvas.height = height;

  const { unproject } = windLayer.params;

  const sw = unproject([0, height]);
  const ne = unproject([width, 0]);
  windCanvas.style.display = 'block';
  d3.select(windCanvas)
    .transition().style('opacity', WIND_OPACITY);

  windLayer.start(
    [[0, 0], [width, height]],
    width,
    height,
    [sw, ne],
  );
  hidden = false;
};

exports.hide = () => {
  if (windCanvas) {
    d3.select(windCanvas).transition().style('opacity', 0)
      .on('end', function() {
        d3.select(this).style('display', 'none');
      });
  }
  if (windLayer) windLayer.stop();
  hidden = true;
};
