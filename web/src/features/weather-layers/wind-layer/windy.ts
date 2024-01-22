// This file was taken from https://github.com/esri/wind-js, and modified

/*  Global class for simulating the movement of particle through a 1km wind grid

    credit: All the credit for this work goes to: https://github.com/cambecc for creating the repo:
      https://github.com/cambecc/earth. The majority of this code is directly take nfrom there, since its awesome.

    This class takes a canvas element and an array of data (1km GFS from http://www.emc.ncep.noaa.gov/index.php?branch=GFS)
    and then uses a mercator (forward/reverse) projection to correctly map wind vectors in "map space".

    The "start" method takes the bounds of the map at its current extent and starts the whole gridding,
    interpolation and animation process.
*/

import { Capacitor } from '@capacitor/core';
import { ForecastEntry, GfsForecastResponse } from 'api/getWeatherData';
import { MapboxMap } from 'react-map-gl';

import { windColor } from './scales';

const VELOCITY_SCALE = 1 / 50_000; //1/70000             // scale for wind velocity (completely arbitrary--this value looks nice)
const MAX_WIND_INTENSITY = 30; // wind velocity at which particle intensity is maximum (m/s)
const MAX_PARTICLE_AGE = 100; // max number of frames a particle is drawn before regeneration
const PARTICLE_LINE_WIDTH = 2; // line width of a drawn particle
const PARTICLE_MULTIPLIER = 8; // particle count scalar (completely arbitrary--this values looks nice)
const PARTICLE_REDUCTION = 0.75; // reduce particle count to this much of normal for mobile devices
const NULL_WIND_VECTOR = [Number.NaN, Number.NaN, null]; // singleton for no wind in the form: [u, v, magnitude]

export type WindVector = [number, number, number | null];

// interpolation for vectors like wind (u,v,m)
export const bilinearInterpolateVector = (
  x: number,
  y: number,
  g00: number[],
  g10: number[],
  g01: number[],
  g11: number[]
): WindVector => {
  const rx = 1 - x;
  const ry = 1 - y;
  const a = rx * ry,
    b = x * ry,
    c = rx * y,
    d = x * y;
  const u = g00[0] * a + g10[0] * b + g01[0] * c + g11[0] * d;
  const v = g00[1] * a + g10[1] * b + g01[1] * c + g11[1] * d;
  return [u, v, Math.hypot(u, v)];
};
/**
 * @returns {Boolean} true if the specified value is not null and not undefined.
 */
const isValue = (x: any): boolean => {
  return x !== null && x !== undefined;
};

/**
 * @returns {Number} returns remainder of floored division, i.e., floor(a / n). Useful for consistent modulo
 * of negative numbers. See http://en.wikipedia.org/wiki/Modulo_operation.
 */
const floorModulus = (a: number, n: number): number => {
  return a - n * Math.floor(a / n);
};

class Grid {
  date: Date;

  lo1: number;
  la1: number;
  dx: number;
  dy: number;
  nx: number;
  ny: number;

  gridData: number[][][];

  constructor(data: GfsForecastResponse) {
    let uComp: ForecastEntry | null = null,
      vComp: ForecastEntry | null = null;

    // Look for recognized parameters in headers
    for (const record of data) {
      const { parameterCategory, parameterNumber } = record.header;
      if (parameterCategory === 2 && parameterNumber === 2) {
        uComp = record;
      } else if (parameterCategory === 2 && parameterNumber === 3) {
        vComp = record;
      }
    }

    // Force assert header - we can't draw wind without it
    const header = (uComp?.header || vComp?.header)!;

    (this.lo1 = header.lo1), (this.la1 = header.la1); // the grid's origin (e.g., 0.0E, 90.0N)
    (this.dx = header.dx), (this.dy = header.dy); // distance between grid points (e.g., 2.5 deg lon, 2.5 deg lat)
    (this.nx = header.nx), (this.ny = header.ny); // number of grid points W-E and N-S (e.g., 144 x 73)

    const date = new Date(header.refTime);
    date.setHours(date.getHours() + header.forecastTime);
    this.date = date;

    this.gridData = this.#buildGrid(uComp?.data ?? [], vComp?.data ?? []);
  }

  #buildGrid(uData: number[], vData: number[]) {
    // Scan mode 0 assumed. Longitude increases from lo1, and latitude decreases from la1.
    // http://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table3-4.shtml
    const grid: number[][][] = [];
    let p = 0;
    const isContinuous = Math.floor(this.nx * this.dx) >= 360;
    for (let index = 0; index < this.ny; index++) {
      const row: number[][] = [];
      for (let index = 0; index < this.nx; index++, p++) {
        row[index] = [uData[p], vData[p]];
      }
      if (isContinuous) {
        // For wrapped grids, duplicate first column as last column to simplify interpolation logic
        row.push(row[0]);
      }
      grid[index] = row;
    }
    return grid;
  }

  interpolate(lo: number, la: number) {
    const loInd = floorModulus(lo - this.lo1, 360) / this.dx; // calculate longitude index in wrapped range [0, 360)
    const laInd = (this.la1 - la) / this.dy; // calculate latitude index in direction +90 to -90

    const fi = Math.floor(loInd),
      ci = fi + 1;
    const fj = Math.floor(laInd),
      cj = fj + 1;

    let row;
    if ((row = this.gridData[fj])) {
      const g00 = row[fi];
      const g10 = row[ci];
      if (isValue(g00) && isValue(g10) && (row = this.gridData[cj])) {
        const g01 = row[fi];
        const g11 = row[ci];
        if (isValue(g01) && isValue(g11)) {
          // All four points found, so interpolate the value.
          return bilinearInterpolateVector(loInd - fi, laInd - fj, g00, g10, g01, g11);
        }
      }
    }
    return null;
  }
}

const buildBounds = (bounds: number[][], width: number, height: number) => {
  const upperLeft = bounds[0];
  const lowerRight = bounds[1];
  const x = Math.round(upperLeft[0]);
  const y = Math.max(Math.floor(upperLeft[1]), 0);
  const yMax = Math.min(Math.ceil(lowerRight[1]), height - 1);
  return { x: x, y: y, yMax: yMax, width: width, height: height };
};

const project = (map: MapboxMap, lat: number, lon: number) => {
  // both in radians, use deg2rad if necessary
  const projected = map.project([lon, lat]);
  return [projected.x, projected.y];
};

const distortion = (map: MapboxMap, λ: number, φ: number, x: number, y: number) => {
  const τ = 2 * Math.PI;
  const H = Math.pow(10, -5.2);
  const hλ = λ < 0 ? H : -H;
  const hφ = φ < 0 ? H : -H;

  const pλ = project(map, φ, λ + hλ);
  const pφ = project(map, φ + hφ, λ);

  // Meridian scale factor (see Snyder, equation 4-3), where R = 1. This handles issue where length of 1º λ
  // changes depending on φ. Without this, there is a pinching effect at the poles.
  const k = Math.cos((φ / 360) * τ);
  return [(pλ[0] - x) / hλ / k, (pλ[1] - y) / hλ / k, (pφ[0] - x) / hφ, (pφ[1] - y) / hφ];
};

/**
 * Calculate distortion of the wind vector caused by the shape of the projection at point (x, y). The wind
 * vector is modified in place and returned by this function.
 */
const distort = (
  map: MapboxMap,
  λ: number,
  φ: number,
  x: number,
  y: number,
  scale: number,
  wind: WindVector
) => {
  const u = wind[0] * scale;
  const v = wind[1] * scale;
  const d = distortion(map, λ, φ, x, y);

  // Scale distortion vectors by u and v, then add.
  wind[0] = d[0] * u + d[2] * v;
  wind[1] = d[1] * u + d[3] * v;
  return wind;
};

const indexFor = (m: number, maxWind: number, resultLength: number) => {
  // map wind speed to a style
  return Math.floor((Math.min(m, maxWind) / maxWind) * (resultLength - 1));
};

export function windIntensityColorScale() {
  return [...windColor.range()];
}

class Field {
  columns: WindVector[][];
  bounds: Bounds;

  constructor(columns: WindVector[][], bounds: Bounds) {
    this.columns = columns;
    this.bounds = bounds;
  }

  /**
   * @returns {Array} wind vector [u, v, magnitude] at the point (x, y), or [NaN, NaN, null] if wind
   *          is undefined at that point.
   */
  getWind(x: number, y: number): WindVector {
    const column = this.columns[Math.round(x)];
    return (column && column[Math.round(y)]) || NULL_WIND_VECTOR;
  }

  // Frees the massive "columns" array for GC. Without this, the array is leaked (in Chrome)
  release() {
    this.columns = [];
  }

  randomizeParticlePosition(o: Particle) {
    // UNDONE: this method is terrible
    let x, y;
    let safetyNet = 0;
    do {
      x = Math.round(Math.floor(Math.random() * this.bounds.width) + this.bounds.x);
      y = Math.round(Math.floor(Math.random() * this.bounds.height) + this.bounds.y);
    } while (this.getWind(x, y)[2] === null && safetyNet++ < 30);
    o.x = x;
    o.y = y;
    return o;
  }
}

class Particle {
  age: number;
  x = 0;
  y = 0;
  xt = 0;
  yt = 0;

  constructor(age: number) {
    this.age = age;
  }
}

interface Bounds {
  width: number;
  x: number;
  y: number;
  height: number;
  yMax: number;
}

export class Windy {
  canvas: HTMLCanvasElement;
  data: GfsForecastResponse;
  map: MapboxMap;

  isMobile: boolean;
  isIphone: boolean;

  started: boolean;
  paused: boolean;

  animationRequest: number | undefined;
  field: Field | undefined;

  constructor(canvas: HTMLCanvasElement, data: GfsForecastResponse, map: MapboxMap) {
    this.canvas = canvas;
    this.data = data;
    this.map = map;

    // true if agent is probably a mobile device. Don't really care if this is accurate.
    this.isMobile = /android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i.test(
      navigator.userAgent
    );
    this.isIphone =
      Capacitor.getPlatform() === 'ios' || /iPad|iPhone|iPod/.test(navigator.userAgent);

    this.started = false;
    this.paused = false;

    this.animationRequest = undefined;
    this.field = undefined;
  }

  invert(x: number, y: number) {
    const object = this.map.unproject([x, y]);

    return [object.lng, object.lat];
  }

  zoomScaling() {
    return 1 / this.map.getZoom();
  }

  interpolateField(
    grid: Grid,
    bounds: Bounds,
    setFieldAndAnimate: (bounds: Bounds, field: Field) => void
  ) {
    const velocityScale = bounds.height * VELOCITY_SCALE * this.zoomScaling();

    const columns: WindVector[][] = [];
    let x = bounds.x;

    const interpolateColumn = (x: number) => {
      const column: WindVector[] = [];
      for (let y = bounds.y; y <= bounds.yMax; y += 2) {
        const coord = this.invert(x, y);

        if (coord) {
          const λ = coord[0],
            φ = coord[1];
          if (Number.isFinite(λ)) {
            let wind = grid.interpolate(λ, φ);
            if (wind) {
              wind = distort(this.map, λ, φ, x, y, velocityScale, wind);
              column[y + 1] = column[y] = wind;
            }
          }
        }
      }
      columns[x + 1] = columns[x] = column;
    };

    (function batchInterpolate() {
      const start = Date.now();
      while (x < bounds.width) {
        interpolateColumn(x);
        x += 2;
        if (Date.now() - start > 1000) {
          setTimeout(batchInterpolate, 25);
          return;
        }
      }
      const field = new Field(columns, bounds);
      setFieldAndAnimate(bounds, field);
    })();
  }

  animate(bounds: Bounds, field: Field) {
    const colorStyles = windIntensityColorScale();
    const buckets: Particle[][] = colorStyles.map(function () {
      return [];
    });

    let particleCount = Math.round(
      bounds.width * PARTICLE_MULTIPLIER * this.zoomScaling()
    );
    if (this.isMobile) {
      particleCount *= PARTICLE_REDUCTION;
    }

    const particles: Particle[] = [];
    for (let index = 0; index < particleCount; index++) {
      particles.push(
        field.randomizeParticlePosition(
          new Particle(Math.floor(Math.random() * MAX_PARTICLE_AGE))
        )
      );
    }

    const computeNextState = () => {
      for (const bucket of buckets) {
        bucket.length = 0;
      }
      for (const particle of particles) {
        if (particle.age > MAX_PARTICLE_AGE) {
          field.randomizeParticlePosition(particle).age = 0;
        }
        const x = particle.x;
        const y = particle.y;
        const v = field.getWind(x, y); // vector at current position
        const m = v[2];
        if (m === null) {
          particle.age = MAX_PARTICLE_AGE; // particle has escaped the grid, never to return...
        } else {
          const xt = x + v[0];
          const yt = y + v[1];
          if (field.getWind(xt, yt)[2] === null) {
            // Particle isn't visible, but it still moves through the field.
            particle.x = xt;
            particle.y = yt;
          } else {
            // Path from (x,y) to (xt,yt) is visible, so add this particle to the appropriate draw bucket.
            particle.xt = xt;
            particle.yt = yt;
            buckets[indexFor(m, MAX_WIND_INTENSITY, colorStyles.length)].push(particle);
          }
        }
        particle.age += 1;
      }
    };

    const renderContext = this.canvas.getContext('2d')!;
    renderContext.lineWidth = PARTICLE_LINE_WIDTH;
    renderContext.fillStyle = '#000';

    let lastFrameTime = Date.now();
    const draw = () => {
      const deltaMs = Date.now() - lastFrameTime;
      // 16 ms ~ 60 fps
      // if we take any longer than that, then scale the opacity
      // inversely with the time
      const b = deltaMs < 16 ? 1 : 16 / deltaMs;

      // Fade existing particle trails.
      renderContext.globalCompositeOperation = this.isIphone
        ? 'destination-out'
        : 'destination-in';
      // This is the parameter concerning the fade property/bug
      renderContext.globalAlpha = Math.pow(0.9, b);
      renderContext.fillRect(bounds.x, bounds.y, bounds.width, bounds.height);
      // Prepare for drawing a new particle
      renderContext.globalCompositeOperation = 'source-over';
      renderContext.globalAlpha = 1;

      // Draw new particle trails.
      for (const bucket of buckets) {
        if (bucket.length > 0) {
          renderContext.beginPath();
          renderContext.strokeStyle = colorStyles[buckets.indexOf(bucket)];
          renderContext.lineWidth = 1 + 0.25 * buckets.indexOf(bucket);
          for (const particle of bucket) {
            renderContext.moveTo(particle.x, particle.y);
            renderContext.lineTo(particle.xt, particle.yt);
            particle.x = particle.xt;
            particle.y = particle.yt;
          }
          renderContext.stroke();
        }
      }
    };

    const frame = () => {
      lastFrameTime = Date.now();
      if (!this.paused) {
        computeNextState();
        draw();
      }
      this.animationRequest = window.requestAnimationFrame(frame);
    };
    frame();
  }

  start(viewportBounds: number[][], width: number, height: number) {
    stop();
    this.started = true;
    this.paused = false;

    const grid = new Grid(this.data);
    this.interpolateField(
      grid,
      buildBounds(viewportBounds, width, height),
      (bounds: Bounds, field: Field) => {
        // animate the canvas with random points
        this.field = field;
        this.animate(bounds, field);
      }
    );
  }

  stop() {
    // Shouldn't be needed anymore, left here in case memory issues somehow occur
    // if (this.field) {
    //   this.field.release();
    // }
    if (this.animationRequest !== undefined) {
      window.cancelAnimationFrame(this.animationRequest);
    }
    this.started = false;
    this.paused = true;
  }
}
