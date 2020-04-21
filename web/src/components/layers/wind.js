/* eslint-disable */
// TODO: remove once refactored

const d3 = Object.assign(
  {},
  require('d3-interpolate'),
  require('d3-selection'),
);

const moment = require('moment');

const global = require('../../global').default;
const grib = require('../../helpers/grib');
const Windy = require('../../helpers/windy');

const WIND_OPACITY = 0.53;

class WindLayer {
  constructor(selectorId) {
    this.canvas = document.getElementById(selectorId);
    this.hidden = true;
    this.lastDraw = null;
    this.windy = null;

    /* This is the *map* transform applied at last render */
    this.initialMapTransform = undefined;

    let zoomEndTimeout = null; // debounce events
    global.zoneMap.onDragStart((transform) => {
      if (this.hidden) { return; }
      if (zoomEndTimeout) {
        // We're already dragging
        clearTimeout(zoomEndTimeout);
        zoomEndTimeout = undefined;
      } else {
        if (this.windy) {
          this.windy.paused = true;
        }
        if (!this.initialMapTransform) {
          this.initialMapTransform = transform;
        }
      }
    });
    global.zoneMap.onDrag((transform) => {
      if (this.hidden) { return; }
      if (!this.initialMapTransform) { return; }
      // `relTransform` is the transform of the map
      // since the last render
      const relScale = transform.k / this.initialMapTransform.k;
      const relTransform = {
        x: (this.initialMapTransform.x * relScale) - transform.x,
        y: (this.initialMapTransform.y * relScale) - transform.y,
        k: relScale,
      };
      this.canvas.style.transform =
        `translate(${relTransform.x}px,${relTransform.y}px) scale(${relTransform.k})`;
    });
    global.zoneMap.onDragEnd(() => {
      if (this.hidden) { return; }
      zoomEndTimeout = setTimeout(() => {
        this.canvas.style.transform = 'inherit';
        this.initialMapTransform = null;
        if (this.windy) {
          this.windy.paused = false;
        }

        // We need to re-update change the projection
        if (!this.windy || this.hidden) { return; }
        const width = parseInt(this.canvas.parentNode.getBoundingClientRect().width, 10);
        const height = parseInt(this.canvas.parentNode.getBoundingClientRect().height, 10);
        const { unproject } = this.windy.params;

        const sw = unproject([0, height]);
        const ne = unproject([width, 0]);

        // Note: the only reason we restart here is to
        // set sw and ne.
        this.windy.start( // Note: this blocks UI..
          [[0, 0], [width, height]],
          width,
          height,
          [sw, ne],
        );
        zoomEndTimeout = undefined;
      }, 500);
    });
  }

  draw(now, gribs1, gribs2, windColor) {
    // Only redraw after 5min
    if (this.lastDraw && (this.lastDraw - new Date().getTime()) < 1000 * 60 * 5) {
      return;
    }

    this.lastDraw = new Date().getTime();

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
      // Only recreate if not already created
      if (!this.windy) {
        this.windy = new Windy({
          canvas: this.canvas,
          project: global.zoneMap.projection(),
          unproject: global.zoneMap.unprojection(),
        });
      }
      this.windy.params.data = interpolatedWind;
    }
  }

  show() {
    if (!this.canvas || !this.windy) { return; }
    if (this.windy && this.windy.started) { return; }
    const width = parseInt(this.canvas.parentNode.getBoundingClientRect().width, 10);
    const height = parseInt(this.canvas.parentNode.getBoundingClientRect().height, 10);
    // Canvas needs to have it's width and height attribute set
    this.canvas.width = width;
    this.canvas.height = height;

    const { unproject } = this.windy.params;

    const sw = unproject([0, height]);
    const ne = unproject([width, 0]);
    this.canvas.style.display = 'block';
    this.canvas.style.opacity = WIND_OPACITY;

    this.windy.start(
      [[0, 0], [width, height]],
      width,
      height,
      [sw, ne],
    );
    this.hidden = false;
  }

  hide() {
    if (this.hidden) return;
    if (this.canvas) {
      this.canvas.style.opacity = 0;
      setTimeout(() => {
        this.canvas.style.display = 'none';
      }, 500);
    }
    if (this.windy) {
      this.windy.stop();
    }
    this.hidden = true;
  }
}

export default WindLayer;
