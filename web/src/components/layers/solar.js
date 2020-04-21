/* eslint-disable */
// TODO: remove once refactored

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-interpolate'),
  require('d3-selection'),
);
const moment = require('moment');
const grib = require('../../helpers/grib');

class SolarLayer {
  constructor(selectorId, map) {
    this.lastDraw = null;
    this.canvas = document.getElementById(selectorId);
    this.hidden = true;
    this.map = map;
    this.k = 0;
    this.grib1 = null;
    this.grib2 = null;

    /* This is the *map* transform applied at last render */
    this.initialMapTransform = undefined;

    let zoomEndTimeout = null; // debounce events
    map.onDragStart((transform) => {
      if (this.hidden) { return; }
      if (zoomEndTimeout) {
        // We're already dragging
        clearTimeout(zoomEndTimeout);
        zoomEndTimeout = undefined;
      } else {
        if (!this.initialMapTransform) {
          this.initialMapTransform = transform;
        }
      }
    });
    map.onDrag((transform) => {
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
    map.onDragEnd(() => {
      if (this.hidden) { return; }
      zoomEndTimeout = setTimeout(() => {
        this.canvas.style.transform = 'inherit';
        this.initialMapTransform = null;
        this.render();
        zoomEndTimeout = undefined;
      }, 500);
    });
  }

  draw(now, argGrib1, argGrib2, callback) {
    // Only redraw after 5min
    if (this.lastDraw && (this.lastDraw - new Date().getTime()) < 1000 * 60 * 5) {
      return callback(null);
    }

    this.lastDraw = new Date().getTime();

    this.grib1 = argGrib1;
    this.grib2 = argGrib2;

    // Interpolates between two solar forecasts<
    const t_before = grib.getTargetTime(this.grib1);
    const t_after = grib.getTargetTime(this.grib2);
    console.log(
      '#1 solar forecast target',
      moment(t_before).fromNow(),
      'made', moment(this.grib1.header.refTime).fromNow());
    console.log(
      '#2 solar forecast target',
      moment(t_after).fromNow(),
      'made', moment(this.grib2.header.refTime).fromNow());
    if (moment(now) > moment(t_after)) {
      return callback(new Error('Error while interpolating solar because current time is out of bounds'));
    }

    this.k = (now - t_before) / (t_after - t_before);

    // (This callback could potentially be done before effects)
    callback(null);

    return this;
  }

  show() {
    if (this.canvas) {
      this.canvas.style.display = 'block';
      this.canvas.style.opacity = 1;
    }
    this.hidden = false;
    this.render();
  }

  hide() {
    if (this.hidden) return;
    if (this.canvas) {
      this.canvas.style.opacity = 0;
      setTimeout(() => {
        this.canvas.style.display = 'none';
      }, 500);
    }
    this.hidden = true;
  }

  render() {
    if (this.hidden || !this.grib1) { return; }

    const { canvas, grib1, grib2, k } = this;
    const unprojection = this.map.unprojection();

    // Control the rendering
    var gaussianBlur = true;
    var continuousScale = true;
    var SOLAR_SCALE = 1000;
    var MAX_OPACITY = 0.85;

    var maxOpacityPix = 256 * MAX_OPACITY;

    // Grib constants
    var Nx = grib1.header.nx;
    var Ny = grib1.header.ny;
    var lo1 = grib1.header.lo1;
    var la1 = grib1.header.la1;
    var dx = grib1.header.dx;
    var dy = grib1.header.dy;

    var ctx = canvas.getContext('2d');
    var realW = parseInt(canvas.parentNode.getBoundingClientRect().width);
    var realH = parseInt(canvas.parentNode.getBoundingClientRect().height);

    if (!realW || !realH) {
        // Don't draw as the canvas has 0 size
        return;
    }
    // Canvas needs to have it's width and height attribute set
    canvas.width = realW;
    canvas.height = realH;

    var ul = this.map.unprojection()([0, 0]);
    var br = this.map.unprojection()([realW, realH]);

    // ** Those need to be integers **
    var minLon = parseInt(Math.floor(ul[0]), 10);
    var maxLon = parseInt(Math.ceil(br[0]), 10);
    var minLat = parseInt(Math.floor(br[1]), 10);
    var maxLat = parseInt(Math.ceil(ul[1]), 10);

    // Blur radius should be about 1deg on screen
    var BLUR_RADIUS = realW / (maxLon - minLon) * 2;

    var h = 100; // number of points in longitude space
    var w = 100; // number of points in latitude space

    // ** Note **
    // We would need better than 1deg data to see the effects at lower scales.

    // Draw initial image
    var imgGrib = ctx.createImageData(w, h);
    // Iterate over lon, lat
    d3.range(0, h).forEach(function (yi) {
        d3.range(0, w).forEach(function (xi) {
            // (x, y) are in (lon, lat) space
            var x = d3.interpolate(minLon, maxLon)((xi + 1) / w);
            var y = d3.interpolate(minLat, maxLat)((yi + 1) / h);

            var i = parseInt(x - lo1 / dx);
            var j = parseInt(la1 - y / dy);
            var n = i + Nx * j;
            var val = d3.interpolate(grib1.data[n], grib2.data[n])(k);

            // (pix_x, pix_y) are in pixel space
            var pix_x = xi;
            var pix_y = h - yi;

            if (continuousScale)
                imgGrib.data[[((pix_y * (imgGrib.width * 4)) + (pix_x * 4)) + 3]] = parseInt(val / SOLAR_SCALE * 255);
            else
                imgGrib.data[[((pix_y * (imgGrib.width * 4)) + (pix_x * 4)) + 3]] = parseInt((0.85 - val / SOLAR_SCALE) * 255);
        });
    });

    // Reproject this image on our projection
    var sourceData = imgGrib.data,
        target = ctx.createImageData(realW, realH),
        targetData = target.data;

    // From https://bl.ocks.org/mbostock/4329423
    // x and y are the coordinate on the new image
    // i is the new image 1D normalized index (R G B Alpha for each pixel)
    // q is the 1D normalize index for the source map
    for (var y = 0, i = -1; y < realH; ++y) {
        for (var x = 0; x < realW; ++x) {
            // (x, y) is in the (final) pixel space

            // We shift the lat/lon so that the truncation result in a rounding
            // p represents the (lon, lat) point we wish to obtain a value for
            var p = unprojection([x, y])//, lon = p[0] + 0.5, lat = p[1] - 0.5;
            var lon = p[0], lat = p[1];

            // if (lon > maxLon || lon < minLon || lat > maxLat || lat < minLat)
            // { i += 4; continue; }

            // q is the index of the associated data point in the other space
            var q = (((maxLat - lat) / (maxLat - minLat)) * h | 0) * w + (((lon - minLon) / (maxLon - minLon)) * w | 0) << 2;

            // Since we are reading the map pixel by pixel we go to the next Alpha channel
            i += 4;
            // Shift source index to alpha
            q += 3;
            targetData[i] = sourceData[q];
        }
    }


    // Apply a gaussian blur on grid cells
    if (gaussianBlur) {
        target = stackBlurImageOpacity(target, 0, 0, realW, realH, BLUR_RADIUS);
    }

    // Apply level of opacity rather than continous scale
    if (continuousScale) {

        var bluredData = target.data,
            next = ctx.createImageData(realW, realH),
            nextData = next.data;

        var i = 3;
        d3.range(realH).forEach(function (y) {
            d3.range(realW).forEach(function (x) {
                // The bluredData correspond to the solar value projected from 0 to 255 hence, 128 is mid-scale
                if (bluredData[i] > 128) {
                    // Gold
                    nextData[i - 3] = 255;
                    nextData[i - 2] = 215;
                    nextData[i - 1] = 0;
                    nextData[i] = maxOpacityPix * (bluredData[i] / 128 - 1);
                }
                else {
                    nextData[i] = maxOpacityPix * (1 - bluredData[i] / 128);
                }

                i += 4;
            });
        });
        target = next;
    }
    ctx.clearRect(0, 0, realW, realH);
    ctx.putImageData(target, 0, 0);
  }

}

module.exports = SolarLayer;


var mul_table = [
  512, 512, 456, 512, 328, 456, 335, 512, 405, 328, 271, 456, 388, 335, 292, 512,
  454, 405, 364, 328, 298, 271, 496, 456, 420, 388, 360, 335, 312, 292, 273, 512,
  482, 454, 428, 405, 383, 364, 345, 328, 312, 298, 284, 271, 259, 496, 475, 456,
  437, 420, 404, 388, 374, 360, 347, 335, 323, 312, 302, 292, 282, 273, 265, 512,
  497, 482, 468, 454, 441, 428, 417, 405, 394, 383, 373, 364, 354, 345, 337, 328,
  320, 312, 305, 298, 291, 284, 278, 271, 265, 259, 507, 496, 485, 475, 465, 456,
  446, 437, 428, 420, 412, 404, 396, 388, 381, 374, 367, 360, 354, 347, 341, 335,
  329, 323, 318, 312, 307, 302, 297, 292, 287, 282, 278, 273, 269, 265, 261, 512,
  505, 497, 489, 482, 475, 468, 461, 454, 447, 441, 435, 428, 422, 417, 411, 405,
  399, 394, 389, 383, 378, 373, 368, 364, 359, 354, 350, 345, 341, 337, 332, 328,
  324, 320, 316, 312, 309, 305, 301, 298, 294, 291, 287, 284, 281, 278, 274, 271,
  268, 265, 262, 259, 257, 507, 501, 496, 491, 485, 480, 475, 470, 465, 460, 456,
  451, 446, 442, 437, 433, 428, 424, 420, 416, 412, 408, 404, 400, 396, 392, 388,
  385, 381, 377, 374, 370, 367, 363, 360, 357, 354, 350, 347, 344, 341, 338, 335,
  332, 329, 326, 323, 320, 318, 315, 312, 310, 307, 304, 302, 299, 297, 294, 292,
  289, 287, 285, 282, 280, 278, 275, 273, 271, 269, 267, 265, 263, 261, 259];

var shg_table = [
  9, 11, 12, 13, 13, 14, 14, 15, 15, 15, 15, 16, 16, 16, 16, 17,
	17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 18, 19,
	19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20,
	20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 21,
	21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
	21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22,
	22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22,
	22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 23,
	23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23,
	23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23,
	23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23,
	23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24,
	24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24,
	24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24,
	24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24,
	24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24];

// Derived from http://www.quasimondo.com/StackBlurForCanvas/StackBlur.js
function stackBlurImageOpacity(imageData, top_x, top_y, width, height, radius) {
    if (isNaN(radius) || radius < 1) return;
    radius |= 0;

    var pixels = imageData.data;

    var x, y, i, p, yp, yi, yw, a_sum, a_out_sum, a_in_sum, pa, rbs;

    var div = radius + radius + 1;
    var w4 = width << 2;
    var widthMinus1 = width - 1;
    var heightMinus1 = height - 1;
    var radiusPlus1 = radius + 1;
    var sumFactor = radiusPlus1 * (radiusPlus1 + 1) / 2;

    var stackStart = new BlurStack();
    var stack = stackStart;
    for (i = 1; i < div; i++) {
        stack = stack.next = new BlurStack();
        if (i == radiusPlus1) var stackEnd = stack;
    }
    stack.next = stackStart;
    var stackIn = null;
    var stackOut = null;

    yw = yi = 0;

    var mul_sum = mul_table[radius];
    var shg_sum = shg_table[radius];

    for (y = 0; y < height; y++) {
        a_in_sum = a_sum = 0;

        a_out_sum = radiusPlus1 * (pa = pixels[yi + 3]);
        a_sum += sumFactor * pa;
        stack = stackStart;

        for (i = 0; i < radiusPlus1; i++) {
            stack.a = pa;
            stack = stack.next;
        }

        for (i = 1; i < radiusPlus1; i++) {
            p = yi + ((widthMinus1 < i ? widthMinus1 : i) << 2);
            a_sum += (stack.a = (pa = pixels[p + 3])) * (rbs = radiusPlus1 - i);
            a_in_sum += pa;
            stack = stack.next;
        }


        stackIn = stackStart;
        stackOut = stackEnd;
        for (x = 0; x < width; x++) {
            pixels[yi + 3] = pa = (a_sum * mul_sum) >> shg_sum;

            a_sum -= a_out_sum;
            a_out_sum -= stackIn.a;

            p = (yw + ((p = x + radius + 1) < widthMinus1 ? p : widthMinus1)) << 2;
            a_in_sum += (stackIn.a = pixels[p + 3]);
            a_sum += a_in_sum;

            stackIn = stackIn.next;

            a_out_sum += (pa = stackOut.a);

            a_in_sum -= pa;

            stackOut = stackOut.next;

            yi += 4;
        }
        yw += width;
    }


    for (x = 0; x < width; x++) {
        a_in_sum = a_sum = 0;

        yi = x << 2;
        a_out_sum = radiusPlus1 * (pa = pixels[yi + 3]);
        a_sum += sumFactor * pa;

        stack = stackStart;

        for (i = 0; i < radiusPlus1; i++) {
            stack.a = pa;
            stack = stack.next;
        }

        yp = width;

        for (i = 1; i <= radius; i++) {
            yi = (yp + x) << 2;

            a_sum += (stack.a = (pa = pixels[yi + 3])) * rbs;

            a_in_sum += pa;

            stack = stack.next;

            if (i < heightMinus1) {
                yp += width;
            }
        }

        yi = x;
        stackIn = stackStart;
        stackOut = stackEnd;
        for (y = 0; y < height; y++) {
            p = yi << 2;
            pixels[p + 3] = pa = (a_sum * mul_sum) >> shg_sum;

            a_sum -= a_out_sum;
            a_out_sum -= stackIn.a;

            p = (x + (((p = y + radiusPlus1) < heightMinus1 ? p : heightMinus1) * width)) << 2;
            a_sum += (a_in_sum += (stackIn.a = pixels[p + 3]));
            stackIn = stackIn.next;
            a_out_sum += (pa = stackOut.a);

            a_in_sum -= pa;

            stackOut = stackOut.next;

            yi += width;
        }
    }
    return imageData;

}

function BlurStack() {
    this.a = 0;
    this.next = null;
}
