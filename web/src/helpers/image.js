/* eslint-disable */
// TODO: remove once refactored

const mul_table = [
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

const shg_table = [
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

function BlurStack() {
  this.a = 0;
  this.next = null;
}

// Derived from http://www.quasimondo.com/StackBlurForCanvas/StackBlur.js
export function stackBlurImageOpacity(imageData, top_x, top_y, width, height, radius) {
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

const MAX_OPACITY = 0.85;

export function scaleImage(source, target) {
  // Pre-calculate the dimension ratios
  const aspectWidth = source.width / target.width;
  const aspectHeight = source.height / target.height;

  for (let tX = 0; tX < target.width; tX += 1) {
    for (let tY = 0; tY < target.height; tY += 1) {
      // Get the source coordinates (sX, sY) given the target coordinates (tX, tY).
      const sX = Math.floor(tX * aspectWidth);
      const sY = Math.floor(tY * aspectHeight);
      // Calculate source and target color indices in the dataset given the coordinates.
      const sIndex = 4 * (sY * source.width + sX);
      const tIndex = 4 * (tY * target.width + tX);
      // Copy only the pixel alpha value.
      target.data[tIndex + 3] = source.data[sIndex + 3];
    }
  }
}


export function applySolarColorFilter(target) {
  for (let i = 0; i < target.data.length; i += 4) {
    // The bluredData correspond to the solar value projected from 0 to 255 hence, 128 is mid-scale
    if (target.data[i + 3] > 128) {
      // Gold
      target.data[i + 0] = 255;
      target.data[i + 1] = 215;
      target.data[i + 2] = 0;
      target.data[i + 3] = 256 * MAX_OPACITY * (target.data[i + 3] / 128 - 1);
    } else {
      target.data[i + 3] = 256 * MAX_OPACITY * (1 - target.data[i + 3] / 128);
    }
  }
}
