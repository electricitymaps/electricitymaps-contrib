var exports = module.exports = {};

var d3 = require('d3');
var moment = require('moment');

var grib = require('./grib');

var solarCanvas;

function bilinearInterpolate(x, y, x1, x2, y1, y2, Q11, Q12, Q21, Q22) {
    var R1 = ((x2 - x) / (x2 - x1)) * Q11 + ((x - x1) / (x2 - x1)) * Q21;
    var R2 = ((x2 - x) / (x2 - x1)) * Q12 + ((x - x1) / (x2 - x1)) * Q22;
    return ((y2 - y) / (y2 - y1)) * R1 + ((y - y1) / (y2 - y1)) * R2;
}

// This is a minified library for image bluring, should be moved to exported Filter in file image_blur, not sure how to properly do this
var mul_table = [512, 512, 456, 512, 328, 456, 335, 512, 405, 328, 271, 456, 388, 335, 292, 512, 454, 405, 364, 328, 298, 271, 496, 456, 420, 388, 360, 335, 312, 292, 273, 512, 482, 454, 428, 405, 383, 364, 345, 328, 312, 298, 284, 271, 259, 496, 475, 456, 437, 420, 404, 388, 374, 360, 347, 335, 323, 312, 302, 292, 282, 273, 265, 512, 497, 482, 468, 454, 441, 428, 417, 405, 394, 383, 373, 364, 354, 345, 337, 328, 320, 312, 305, 298, 291, 284, 278, 271, 265, 259, 507, 496, 485, 475, 465, 456, 446, 437, 428, 420, 412, 404, 396, 388, 381, 374, 367, 360, 354, 347, 341, 335, 329, 323, 318, 312, 307, 302, 297, 292, 287, 282, 278, 273, 269, 265, 261, 512, 505, 497, 489, 482, 475, 468, 461, 454, 447, 441, 435, 428, 422, 417, 411, 405, 399, 394, 389, 383, 378, 373, 368, 364, 359, 354, 350, 345, 341, 337, 332, 328, 324, 320, 316, 312, 309, 305, 301, 298, 294, 291, 287, 284, 281, 278, 274, 271, 268, 265, 262, 259, 257, 507, 501, 496, 491, 485, 480, 475, 470, 465, 460, 456, 451, 446, 442, 437, 433, 428, 424, 420, 416, 412, 408, 404, 400, 396, 392, 388, 385, 381, 377, 374, 370, 367, 363, 360, 357, 354, 350, 347, 344, 341, 338, 335, 332, 329, 326, 323, 320, 318, 315, 312, 310, 307, 304, 302, 299, 297, 294, 292, 289, 287, 285, 282, 280, 278, 275, 273, 271, 269, 267, 265, 263, 261, 259]; var shg_table = [9, 11, 12, 13, 13, 14, 14, 15, 15, 15, 15, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24, 24]; function stackBlurImage(imageID, canvasID, radius, blurAlphaChannel) { var img = document.getElementById(imageID); var w = img.naturalWidth; var h = img.naturalHeight; var canvas = document.getElementById(canvasID); canvas.style.width = w + "px"; canvas.style.height = h + "px"; canvas.width = w; canvas.height = h; var context = canvas.getContext("2d"); context.clearRect(0, 0, w, h); context.drawImage(img, 0, 0); if (isNaN(radius) || radius < 1) return; if (blurAlphaChannel) stackBlurCanvasRGBA(canvasID, 0, 0, w, h, radius); else stackBlurCanvasRGB(canvasID, 0, 0, w, h, radius) } function stackBlurCanvasRGBA(id, top_x, top_y, width, height, radius) { if (isNaN(radius) || radius < 1) return; radius |= 0; var canvas = document.getElementById(id); var context = canvas.getContext("2d"); var imageData; try { try { imageData = context.getImageData(top_x, top_y, width, height) } catch (e) { try { netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead"); imageData = context.getImageData(top_x, top_y, width, height) } catch (e) { alert("Cannot access local image"); throw new Error("unable to access local image data: " + e); return } } } catch (e) { alert("Cannot access image"); throw new Error("unable to access image data: " + e) } var pixels = imageData.data; var x, y, i, p, yp, yi, yw, r_sum, g_sum, b_sum, a_sum, r_out_sum, g_out_sum, b_out_sum, a_out_sum, r_in_sum, g_in_sum, b_in_sum, a_in_sum, pr, pg, pb, pa, rbs; var div = radius + radius + 1; var w4 = width << 2; var widthMinus1 = width - 1; var heightMinus1 = height - 1; var radiusPlus1 = radius + 1; var sumFactor = radiusPlus1 * (radiusPlus1 + 1) / 2; var stackStart = new BlurStack; var stack = stackStart; for (i = 1; i < div; i++) { stack = stack.next = new BlurStack; if (i == radiusPlus1) var stackEnd = stack } stack.next = stackStart; var stackIn = null; var stackOut = null; yw = yi = 0; var mul_sum = mul_table[radius]; var shg_sum = shg_table[radius]; for (y = 0; y < height; y++) { r_in_sum = g_in_sum = b_in_sum = a_in_sum = r_sum = g_sum = b_sum = a_sum = 0; r_out_sum = radiusPlus1 * (pr = pixels[yi]); g_out_sum = radiusPlus1 * (pg = pixels[yi + 1]); b_out_sum = radiusPlus1 * (pb = pixels[yi + 2]); a_out_sum = radiusPlus1 * (pa = pixels[yi + 3]); r_sum += sumFactor * pr; g_sum += sumFactor * pg; b_sum += sumFactor * pb; a_sum += sumFactor * pa; stack = stackStart; for (i = 0; i < radiusPlus1; i++) { stack.r = pr; stack.g = pg; stack.b = pb; stack.a = pa; stack = stack.next } for (i = 1; i < radiusPlus1; i++) { p = yi + ((widthMinus1 < i ? widthMinus1 : i) << 2); r_sum += (stack.r = pr = pixels[p]) * (rbs = radiusPlus1 - i); g_sum += (stack.g = pg = pixels[p + 1]) * rbs; b_sum += (stack.b = pb = pixels[p + 2]) * rbs; a_sum += (stack.a = pa = pixels[p + 3]) * rbs; r_in_sum += pr; g_in_sum += pg; b_in_sum += pb; a_in_sum += pa; stack = stack.next } stackIn = stackStart; stackOut = stackEnd; for (x = 0; x < width; x++) { pixels[yi + 3] = pa = a_sum * mul_sum >> shg_sum; if (pa != 0) { pa = 255 / pa; pixels[yi] = (r_sum * mul_sum >> shg_sum) * pa; pixels[yi + 1] = (g_sum * mul_sum >> shg_sum) * pa; pixels[yi + 2] = (b_sum * mul_sum >> shg_sum) * pa } else { pixels[yi] = pixels[yi + 1] = pixels[yi + 2] = 0 } r_sum -= r_out_sum; g_sum -= g_out_sum; b_sum -= b_out_sum; a_sum -= a_out_sum; r_out_sum -= stackIn.r; g_out_sum -= stackIn.g; b_out_sum -= stackIn.b; a_out_sum -= stackIn.a; p = yw + ((p = x + radius + 1) < widthMinus1 ? p : widthMinus1) << 2; r_in_sum += stackIn.r = pixels[p]; g_in_sum += stackIn.g = pixels[p + 1]; b_in_sum += stackIn.b = pixels[p + 2]; a_in_sum += stackIn.a = pixels[p + 3]; r_sum += r_in_sum; g_sum += g_in_sum; b_sum += b_in_sum; a_sum += a_in_sum; stackIn = stackIn.next; r_out_sum += pr = stackOut.r; g_out_sum += pg = stackOut.g; b_out_sum += pb = stackOut.b; a_out_sum += pa = stackOut.a; r_in_sum -= pr; g_in_sum -= pg; b_in_sum -= pb; a_in_sum -= pa; stackOut = stackOut.next; yi += 4 } yw += width } for (x = 0; x < width; x++) { g_in_sum = b_in_sum = a_in_sum = r_in_sum = g_sum = b_sum = a_sum = r_sum = 0; yi = x << 2; r_out_sum = radiusPlus1 * (pr = pixels[yi]); g_out_sum = radiusPlus1 * (pg = pixels[yi + 1]); b_out_sum = radiusPlus1 * (pb = pixels[yi + 2]); a_out_sum = radiusPlus1 * (pa = pixels[yi + 3]); r_sum += sumFactor * pr; g_sum += sumFactor * pg; b_sum += sumFactor * pb; a_sum += sumFactor * pa; stack = stackStart; for (i = 0; i < radiusPlus1; i++) { stack.r = pr; stack.g = pg; stack.b = pb; stack.a = pa; stack = stack.next } yp = width; for (i = 1; i <= radius; i++) { yi = yp + x << 2; r_sum += (stack.r = pr = pixels[yi]) * (rbs = radiusPlus1 - i); g_sum += (stack.g = pg = pixels[yi + 1]) * rbs; b_sum += (stack.b = pb = pixels[yi + 2]) * rbs; a_sum += (stack.a = pa = pixels[yi + 3]) * rbs; r_in_sum += pr; g_in_sum += pg; b_in_sum += pb; a_in_sum += pa; stack = stack.next; if (i < heightMinus1) { yp += width } } yi = x; stackIn = stackStart; stackOut = stackEnd; for (y = 0; y < height; y++) { p = yi << 2; pixels[p + 3] = pa = a_sum * mul_sum >> shg_sum; if (pa > 0) { pa = 255 / pa; pixels[p] = (r_sum * mul_sum >> shg_sum) * pa; pixels[p + 1] = (g_sum * mul_sum >> shg_sum) * pa; pixels[p + 2] = (b_sum * mul_sum >> shg_sum) * pa } else { pixels[p] = pixels[p + 1] = pixels[p + 2] = 0 } r_sum -= r_out_sum; g_sum -= g_out_sum; b_sum -= b_out_sum; a_sum -= a_out_sum; r_out_sum -= stackIn.r; g_out_sum -= stackIn.g; b_out_sum -= stackIn.b; a_out_sum -= stackIn.a; p = x + ((p = y + radiusPlus1) < heightMinus1 ? p : heightMinus1) * width << 2; r_sum += r_in_sum += stackIn.r = pixels[p]; g_sum += g_in_sum += stackIn.g = pixels[p + 1]; b_sum += b_in_sum += stackIn.b = pixels[p + 2]; a_sum += a_in_sum += stackIn.a = pixels[p + 3]; stackIn = stackIn.next; r_out_sum += pr = stackOut.r; g_out_sum += pg = stackOut.g; b_out_sum += pb = stackOut.b; a_out_sum += pa = stackOut.a; r_in_sum -= pr; g_in_sum -= pg; b_in_sum -= pb; a_in_sum -= pa; stackOut = stackOut.next; yi += width } } context.putImageData(imageData, top_x, top_y) } function stackBlurCanvasRGB(id, top_x, top_y, width, height, radius) { if (isNaN(radius) || radius < 1) return; radius |= 0; var canvas = document.getElementById(id); var context = canvas.getContext("2d"); var imageData; try { try { imageData = context.getImageData(top_x, top_y, width, height) } catch (e) { try { netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead"); imageData = context.getImageData(top_x, top_y, width, height) } catch (e) { alert("Cannot access local image"); throw new Error("unable to access local image data: " + e); return } } } catch (e) { alert("Cannot access image"); throw new Error("unable to access image data: " + e) } var pixels = imageData.data; var x, y, i, p, yp, yi, yw, r_sum, g_sum, b_sum, r_out_sum, g_out_sum, b_out_sum, r_in_sum, g_in_sum, b_in_sum, pr, pg, pb, rbs; var div = radius + radius + 1; var w4 = width << 2; var widthMinus1 = width - 1; var heightMinus1 = height - 1; var radiusPlus1 = radius + 1; var sumFactor = radiusPlus1 * (radiusPlus1 + 1) / 2; var stackStart = new BlurStack; var stack = stackStart; for (i = 1; i < div; i++) { stack = stack.next = new BlurStack; if (i == radiusPlus1) var stackEnd = stack } stack.next = stackStart; var stackIn = null; var stackOut = null; yw = yi = 0; var mul_sum = mul_table[radius]; var shg_sum = shg_table[radius]; for (y = 0; y < height; y++) { r_in_sum = g_in_sum = b_in_sum = r_sum = g_sum = b_sum = 0; r_out_sum = radiusPlus1 * (pr = pixels[yi]); g_out_sum = radiusPlus1 * (pg = pixels[yi + 1]); b_out_sum = radiusPlus1 * (pb = pixels[yi + 2]); r_sum += sumFactor * pr; g_sum += sumFactor * pg; b_sum += sumFactor * pb; stack = stackStart; for (i = 0; i < radiusPlus1; i++) { stack.r = pr; stack.g = pg; stack.b = pb; stack = stack.next } for (i = 1; i < radiusPlus1; i++) { p = yi + ((widthMinus1 < i ? widthMinus1 : i) << 2); r_sum += (stack.r = pr = pixels[p]) * (rbs = radiusPlus1 - i); g_sum += (stack.g = pg = pixels[p + 1]) * rbs; b_sum += (stack.b = pb = pixels[p + 2]) * rbs; r_in_sum += pr; g_in_sum += pg; b_in_sum += pb; stack = stack.next } stackIn = stackStart; stackOut = stackEnd; for (x = 0; x < width; x++) { pixels[yi] = r_sum * mul_sum >> shg_sum; pixels[yi + 1] = g_sum * mul_sum >> shg_sum; pixels[yi + 2] = b_sum * mul_sum >> shg_sum; r_sum -= r_out_sum; g_sum -= g_out_sum; b_sum -= b_out_sum; r_out_sum -= stackIn.r; g_out_sum -= stackIn.g; b_out_sum -= stackIn.b; p = yw + ((p = x + radius + 1) < widthMinus1 ? p : widthMinus1) << 2; r_in_sum += stackIn.r = pixels[p]; g_in_sum += stackIn.g = pixels[p + 1]; b_in_sum += stackIn.b = pixels[p + 2]; r_sum += r_in_sum; g_sum += g_in_sum; b_sum += b_in_sum; stackIn = stackIn.next; r_out_sum += pr = stackOut.r; g_out_sum += pg = stackOut.g; b_out_sum += pb = stackOut.b; r_in_sum -= pr; g_in_sum -= pg; b_in_sum -= pb; stackOut = stackOut.next; yi += 4 } yw += width } for (x = 0; x < width; x++) { g_in_sum = b_in_sum = r_in_sum = g_sum = b_sum = r_sum = 0; yi = x << 2; r_out_sum = radiusPlus1 * (pr = pixels[yi]); g_out_sum = radiusPlus1 * (pg = pixels[yi + 1]); b_out_sum = radiusPlus1 * (pb = pixels[yi + 2]); r_sum += sumFactor * pr; g_sum += sumFactor * pg; b_sum += sumFactor * pb; stack = stackStart; for (i = 0; i < radiusPlus1; i++) { stack.r = pr; stack.g = pg; stack.b = pb; stack = stack.next } yp = width; for (i = 1; i <= radius; i++) { yi = yp + x << 2; r_sum += (stack.r = pr = pixels[yi]) * (rbs = radiusPlus1 - i); g_sum += (stack.g = pg = pixels[yi + 1]) * rbs; b_sum += (stack.b = pb = pixels[yi + 2]) * rbs; r_in_sum += pr; g_in_sum += pg; b_in_sum += pb; stack = stack.next; if (i < heightMinus1) { yp += width } } yi = x; stackIn = stackStart; stackOut = stackEnd; for (y = 0; y < height; y++) { p = yi << 2; pixels[p] = r_sum * mul_sum >> shg_sum; pixels[p + 1] = g_sum * mul_sum >> shg_sum; pixels[p + 2] = b_sum * mul_sum >> shg_sum; r_sum -= r_out_sum; g_sum -= g_out_sum; b_sum -= b_out_sum; r_out_sum -= stackIn.r; g_out_sum -= stackIn.g; b_out_sum -= stackIn.b; p = x + ((p = y + radiusPlus1) < heightMinus1 ? p : heightMinus1) * width << 2; r_sum += r_in_sum += stackIn.r = pixels[p]; g_sum += g_in_sum += stackIn.g = pixels[p + 1]; b_sum += b_in_sum += stackIn.b = pixels[p + 2]; stackIn = stackIn.next; r_out_sum += pr = stackOut.r; g_out_sum += pg = stackOut.g; b_out_sum += pb = stackOut.b; r_in_sum -= pr; g_in_sum -= pg; b_in_sum -= pb; stackOut = stackOut.next; yi += width } } context.putImageData(imageData, top_x, top_y) } function BlurStack() { this.r = 0; this.g = 0; this.b = 0; this.a = 0; this.next = null }

exports.isExpired = function (now, grib1, grib2) {
    return grib.getTargetTime(grib2) <= moment(now) || grib.getTargetTime(grib1) > moment(now);
}

exports.draw = function (canvasSelector, now, grib1, grib2, solarColor, projection, callback) {

    // Control the rendering
    var gaussianBlur = true;
    var levels = false;

    // Interpolates between two solar forecasts<
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


    var k = (now - t_before) / (t_after - t_before);
    var buckets = d3.range(solarColor.range().length)
        .map(function (d) { return []; });
    var bucketIndex = d3.scaleLinear()
        .rangeRound(d3.range(buckets.length))
        .domain(solarColor.domain())
        .clamp(true);
    var solarScale = solarColor.domain()[solarColor.domain().length - 1];

    var k = (now - t_before) / (t_after - t_before);
    if (!k || !isFinite(k)) k = 0;

    var Nx = grib1.header.nx;
    var Ny = grib1.header.ny;
    var lo1 = grib1.header.lo1;
    var la1 = grib1.header.la1;
    var dx = grib1.header.dx;
    var dy = grib1.header.dy;

    var BLUR_RADIUS = 20;

    var alphas = solarColor.range().map(function (d) {
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


    // Set our domain
    var NE = projection.invert([realW, 0])
    var NW = projection.invert([0, 0])
    var SW = projection.invert([realW, realH])
    var SE = projection.invert([0, realH])
    var S = projection.invert([realW / 2, realH])
    var N = projection.invert([realW / 2, 0])
    N[1] = 80;

    var minLat = Math.ceil(SE[1]);
    var maxLat = Math.floor(N[1]);
    var minLon = Math.ceil(NW[0]);
    var maxLon = Math.floor(NE[0]);
    h = maxLat - minLat;
    w = maxLon - minLon;

    var dt = new Date().getTime();
    console.log('Draw solar start:' + new Date())

    // Draw initial image (1px 1deg) from grib
    var imgGrib = ctx.createImageData(w, h);
    d3.range(minLat, maxLat).forEach(function (y) {
        d3.range(minLon, maxLon).forEach(function (x) {

            var i = parseInt(x - lo1) / dx;
            var j = parseInt(la1 - y) / dy;
            var n = i + Nx * j;
            var val = d3.interpolate(grib1.data[n], grib2.data[n])(k);

            var pix_x = x - minLon;
            var pix_y = h - (y - minLat);

            if (levels)
                imgGrib.data[[((pix_y * (imgGrib.width * 4)) + (pix_x * 4)) + 3]] = parseInt(val / solarScale * 255);
            else
                imgGrib.data[[((pix_y * (imgGrib.width * 4)) + (pix_x * 4)) + 3]] = parseInt((0.85 - val / solarScale) * 255);
        });
    });
    solarCanvas.attr('height', h);
    solarCanvas.attr('width', w);

    ctx.clearRect(0, 0, h, w);
    ctx.putImageData(imgGrib, 0, 0);

    console.log('Extract grib:' + (new Date().getTime() - dt));
    dt = new Date().getTime();

    // Reproject this image on our projection
    var sourceData = ctx.getImageData(0, 0, w, h).data,
        target = ctx.createImageData(realW, realH),
        targetData = target.data;

    for (var y = 0, i = -1; y < realH; ++y) {
        for (var x = 0; x < realW; ++x) {
            var p = projection.invert([x, y]), lon = p[0], lat = p[1];
            if (lon > maxLon || lon < minLon || lat > maxLat || lat < minLat) { i += 4; continue; }
            var q = ((maxLat - lat) / (maxLat - minLat) * h | 0) * w + ((lon - minLon) / (maxLon - minLon) * w | 0) << 2;
            i += 3;
            q += 2;
            targetData[++i] = sourceData[++q];
        }
    }

    ctx.clearRect(0, 0, w, h);
    solarCanvas.attr('height', realH);
    solarCanvas.attr('width', realW);
    ctx.putImageData(target, 1, 1);
    console.log('Reroject time:' + (new Date().getTime() - dt));

    // Apply a gaussian blur on grid cells
    if (gaussianBlur) {
        dt = new Date().getTime();

        stackBlurCanvasRGBA(solarCanvas._groups[0][0].id, 0, 0, realW, realH, BLUR_RADIUS);
        console.log('Blur time:' + (new Date().getTime() - dt));
    }

    // Apply level of opacity rather than continous scale
    if (levels) {
        dt = new Date().getTime();

        var bluredData = ctx.getImageData(0, 0, realW, realH).data,
            target = ctx.createImageData(realW, realH),
            targetData = target.data;

        var i = 3;
        d3.range(realH).forEach(function (y) {
            d3.range(realW).forEach(function (x) {
                targetData[i] = parseInt(alphas[bucketIndex(bluredData[i] * solarScale / 255)] * 255);
                i += 4;
            });
        });
        ctx.clearRect(0, 0, realW, realH);
        ctx.putImageData(target, 0, 0);
        console.log('Level time:' + (new Date().getTime() - dt));
    }

    callback(null);
};

exports.show = function () {
    solarCanvas.transition().style('opacity', 1);
}

exports.hide = function () {
    if (solarCanvas) solarCanvas.transition().style('opacity', 0);
}
