/* eslint-disable unicorn/no-abusive-eslint-disable */
/* eslint-disable */
// @ts-nocheck
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
import { MapboxMap } from 'react-map-gl';

import { windColor } from './scales';

const VELOCITY_SCALE = 1 / 50_000; //1/70000             // scale for wind velocity (completely arbitrary--this value looks nice)
const MAX_WIND_INTENSITY = 30; // wind velocity at which particle intensity is maximum (m/s)
const MAX_PARTICLE_AGE = 100; // max number of frames a particle is drawn before regeneration
const PARTICLE_LINE_WIDTH = 2; // line width of a drawn particle
const PARTICLE_MULTIPLIER = 8; // particle count scalar (completely arbitrary--this values looks nice)
const PARTICLE_REDUCTION = 0.75; // reduce particle count to this much of normal for mobile devices
const NULL_WIND_VECTOR = [Number.NaN, Number.NaN, null]; // singleton for no wind in the form: [u, v, magnitude]

// interpolation for vectors like wind (u,v,m)
export const bilinearInterpolateVector = (
  x: number,
  y: number,
  g00: number[],
  g10: number[],
  g01: number[],
  g11: number[]
) => {
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

const createWindBuilder = (
  uComp: { data: any; header: any } | null,
  vComp: { data: any } | null
) => {
  const uData = uComp?.data,
    vData = vComp?.data;
  return {
    header: uComp?.header,
    //recipe: recipeFor("wind-" + uComp.header.surface1Value),
    data: function (index: string | number) {
      return [uData[index], vData[index]];
    },
    interpolate: bilinearInterpolateVector,
  };
};

const createBuilder = (data: any[]) => {
  let uComp = null,
    vComp = null;
  for (const record of data) {
    const { parameterCategory, parameterNumber } = record.header;
    if (parameterCategory === 2 && parameterNumber === 2) {
      uComp = record;
    } else if (parameterCategory === 2 && parameterNumber === 3) {
      vComp = record;
    }
  }

  return createWindBuilder(uComp, vComp);
};

/**
 * @returns {Boolean} true if the specified value is not null and not undefined.
 */
const isValue = (x: null | undefined): boolean => {
  return x !== null && x !== undefined;
};

/**
 * @returns {Number} returns remainder of floored division, i.e., floor(a / n). Useful for consistent modulo
 * of negative numbers. See http://en.wikipedia.org/wiki/Modulo_operation.
 */
const floorModulus = (a: number, n: number): number => {
  return a - n * Math.floor(a / n);
};

const buildGrid = (
  data: any,
  callback: {
    (grid: any): void;
    (argument0: { date: Date; interpolate: (λ: any, φ: any) => number[] | null }): void;
  }
) => {
  const builder = createBuilder(data);

  const header = builder.header;
  const λ0 = header.lo1,
    φ0 = header.la1; // the grid's origin (e.g., 0.0E, 90.0N)
  const Δλ = header.dx,
    Δφ = header.dy; // distance between grid points (e.g., 2.5 deg lon, 2.5 deg lat)
  const ni = header.nx,
    nj = header.ny; // number of grid points W-E and N-S (e.g., 144 x 73)
  const date = new Date(header.refTime);
  date.setHours(date.getHours() + header.forecastTime);

  // Scan mode 0 assumed. Longitude increases from λ0, and latitude decreases from φ0.
  // http://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table3-4.shtml
  const grid: any[] = [];
  let p = 0;
  const isContinuous = Math.floor(ni * Δλ) >= 360;
  for (let index = 0; index < nj; index++) {
    const row = [];
    for (let index = 0; index < ni; index++, p++) {
      row[index] = builder.data(p);
    }
    if (isContinuous) {
      // For wrapped grids, duplicate first column as last column to simplify interpolation logic
      row.push(row[0]);
    }
    grid[index] = row;
  }

  function interpolate(λ: number, φ: number) {
    const index = floorModulus(λ - λ0, 360) / Δλ; // calculate longitude index in wrapped range [0, 360)
    const index_ = (φ0 - φ) / Δφ; // calculate latitude index in direction +90 to -90

    const fi = Math.floor(index),
      ci = fi + 1;
    const fj = Math.floor(index_),
      cj = fj + 1;

    let row;
    if ((row = grid[fj])) {
      const g00 = row[fi];
      const g10 = row[ci];
      if (isValue(g00) && isValue(g10) && (row = grid[cj])) {
        const g01 = row[fi];
        const g11 = row[ci];
        if (isValue(g01) && isValue(g11)) {
          // All four points found, so interpolate the value.
          return builder.interpolate(index - fi, index_ - fj, g00, g10, g01, g11);
        }
      }
    }
    return null;
  }
  callback({
    date: date,
    interpolate: interpolate,
  });
};

const buildBounds = (bounds: any[], width: any, height: number) => {
  const upperLeft = bounds[0];
  const lowerRight = bounds[1];
  const x = Math.round(upperLeft[0]); //Math.max(Math.floor(upperLeft[0], 0), 0);
  const y = Math.max(Math.floor(upperLeft[1], 0), 0);
  const yMax = Math.min(Math.ceil(lowerRight[1], height), height - 1);
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
  wind: [number, number]
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

const createField = function (
  columns: any[],
  bounds: { width: number; x: number; height: number; y: number },
  callback: (
    argument0: any,
    argument1: {
      (x: any, y: any): any;
      // Frees the massive "columns" array for GC. Without this, the array is leaked (in Chrome) each time a new
      // field is interpolated because the field closure's context is leaked, for reasons that defy explanation.
      release(): void;
      randomize(o: any): any;
    }
  ) => void
) {
  /**
   * @returns {Array} wind vector [u, v, magnitude] at the point (x, y), or [NaN, NaN, null] if wind
   *          is undefined at that point.
   */
  function field(x: number, y: number): Array<any> {
    const column = columns[Math.round(x)];
    return (column && column[Math.round(y)]) || NULL_WIND_VECTOR;
  }

  // Frees the massive "columns" array for GC. Without this, the array is leaked (in Chrome) each time a new
  // field is interpolated because the field closure's context is leaked, for reasons that defy explanation.
  field.release = function () {
    columns = [];
  };

  field.randomize = function (o: { x: number; y: number }) {
    // UNDONE: this method is terrible
    let x, y;
    let safetyNet = 0;
    do {
      x = Math.round(Math.floor(Math.random() * bounds.width) + bounds.x);
      y = Math.round(Math.floor(Math.random() * bounds.height) + bounds.y);
    } while (field(x, y)[2] === null && safetyNet++ < 30);
    o.x = x;
    o.y = y;
    return o;
  };

  callback(bounds, field);
};

function deg2rad(deg: number) {
  return (deg / 180) * Math.PI;
}

interface Particle {
  age: number;
  x?: number;
  y?: number;
  xt?: number;
  yt?: number;
}

export class Windy {
  canvas: HTMLCanvasElement;
  data: any;
  map: MapboxMap;

  isMobile: boolean;
  isIphone: boolean;

  started: boolean;
  paused: boolean;

  animationRequest: any;
  field: any;

  constructor(canvas: HTMLCanvasElement, data: any, map: MapboxMap) {
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

  invert(x: any, y: any) {
    const object = this.map.unproject([x, y]);

    return [object.lng, object.lat];
  }

  zoomScaling() {
    return 1 / Math.sqrt(this.map.transform.scale);
  }

  interpolateField(
    grid: { interpolate: (argument0: any, argument1: any) => any },
    bounds: { x: any; y: any; yMax: any; width: any; height: any },
    extent: {
      south: number;
      north: number;
      east: number;
      west: number;
      width: any;
      height: any;
    },
    callback: (bounds: number[][], field: any) => void
  ) {
    const velocityScale = bounds.height * VELOCITY_SCALE * this.zoomScaling();

    const columns: never[] = [];
    let x = bounds.x;

    const interpolateColumn = (x: number) => {
      const column = [];
      for (let y = bounds.y; y <= bounds.yMax; y += 2) {
        const coord = this.invert(x, y, extent);

        if (coord) {
          const λ = coord[0],
            φ = coord[1];
          if (isFinite(λ)) {
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
          //MAX_TASK_TIME) {
          setTimeout(batchInterpolate, 25);
          return;
        }
      }
      createField(columns, bounds, callback);
    })();
  }

  animate(
    bounds: { width: number; x: any; y: any; height: any },
    field: {
      (argument0: any, argument1: any): null[];
      (argument0: any, argument1: any): null[];
      randomize: any;
    }
  ) {
    const colorStyles = windIntensityColorScale();
    const buckets: any[][] = colorStyles.map(function () {
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
        field.randomize({ age: Math.floor(Math.random() * MAX_PARTICLE_AGE) + 0 })
      );
    }

    const computeNextState = () => {
      for (const bucket of buckets) {
        bucket.length = 0;
      }
      for (const particle of particles) {
        if (particle.age > MAX_PARTICLE_AGE) {
          field.randomize(particle).age = 0;
        }
        const x = particle.x;
        const y = particle.y;
        const v = field(x, y); // vector at current position
        const m = v[2];
        if (m === null) {
          particle.age = MAX_PARTICLE_AGE; // particle has escaped the grid, never to return...
        } else {
          const xt = x + v[0];
          const yt = y + v[1];
          if (field(xt, yt)[2] === null) {
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

    console.log('yo', buckets);

    const frame = () => {
      lastFrameTime = Date.now();
      if (!this.paused) {
        computeNextState();
        draw();
      }
      this.animationRequest = requestAnimationFrame(frame);
    };
    frame();
  }

  start(bounds: number[][], width: any, height: any, extent: any[][]) {
    const mapBounds = {
      south: deg2rad(extent[0][1]),
      north: deg2rad(extent[1][1]),
      east: deg2rad(extent[1][0]),
      west: deg2rad(extent[0][0]),
      width: width,
      height: height,
    };

    stop();
    this.started = true;
    this.paused = false;

    buildGrid(this.data, (grid: any) => {
      this.interpolateField(
        grid,
        buildBounds(bounds, width, height),
        mapBounds,
        (bounds: number[][], field: any) => {
          // animate the canvas with random points
          this.field = field;
          this.animate(bounds, field);
        }
      );
    });
  }

  stop() {
    if (this.field) {
      this.field.release();
    }
    if (this.animationRequest) {
      cancelAnimationFrame(this.animationRequest);
    }
    this.started = false;
    this.paused = true;
  }
}
