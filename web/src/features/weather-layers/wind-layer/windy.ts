// This file was taken from https://github.com/esri/wind-js, and modified

/*  Global class for simulating the movement of particle through a 1km wind grid

    credit: All the credit for this work goes to: https://github.com/cambecc for creating the repo:
      https://github.com/cambecc/earth. The majority of this code is directly take nfrom there, since its awesome.

    This class takes a canvas element and an array of data (1km GFS from http://www.emc.ncep.noaa.gov/index.php?branch=GFS)
    and then uses a mercator (forward/reverse) projection to correctly map wind vectors in "map space".

    The "start" method takes the bounds of the map at its current extent and starts the whole gridding,
    interpolation and animation process.
*/

import { GfsForecastResponse } from 'api/getWeatherData';

import { buildBounds, distort, WindVector } from './calc';
import Field from './Field';
import Grid from './Grid';
import { MAX_WIND, windIntensityColorScale } from './scales';
import { isMobile } from './util';

const VELOCITY_SCALE = 1 / 50_000; //1/70000             // scale for wind velocity (completely arbitrary--this value looks nice)
const MAX_WIND_INTENSITY = MAX_WIND; // wind velocity at which particle intensity is maximum (m/s)
const MAX_PARTICLE_AGE = 100; // max number of frames a particle is drawn before regeneration
const PARTICLE_LINE_WIDTH = 2; // line width of a drawn particle
const PARTICLE_MULTIPLIER = 8; // particle count scalar (completely arbitrary--this values looks nice)
const PARTICLE_REDUCTION = 0.75; // reduce particle count to this much of normal for mobile devices

export const NULL_WIND_VECTOR = [Number.NaN, Number.NaN, Number.NaN]; // singleton for no wind in the form: [u, v, magnitude]

export interface Bounds {
  width: number;
  height: number;
  x: number;
  y: number;
  yMax: number;
}

export class Particle {
  age: number;
  x = 0;
  y = 0;
  xt = 0;
  yt = 0;

  constructor(age: number) {
    this.age = age;
  }
}

/**
 * Oversees animation of particles
 */
export class Windy {
  canvas: HTMLCanvasElement;
  data: GfsForecastResponse;
  map: maplibregl.Map;

  started: boolean;
  paused: boolean;

  animationRequest: number | undefined;
  field: Field | undefined;

  constructor(canvas: HTMLCanvasElement, data: GfsForecastResponse, map: maplibregl.Map) {
    this.canvas = canvas;
    this.data = data;
    this.map = map;

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
    if (isMobile()) {
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
        if (Number.isNaN(m)) {
          particle.age = MAX_PARTICLE_AGE; // particle has escaped the grid, never to return...
        } else {
          const xt = x + v[0];
          const yt = y + v[1];
          if (Number.isNaN(field.getWind(xt, yt)[2])) {
            // Particle isn't visible, but it still moves through the field.
            particle.x = xt;
            particle.y = yt;
          } else {
            // Path from (x,y) to (xt,yt) is visible, so add this particle to the appropriate draw bucket.
            particle.xt = xt;
            particle.yt = yt;
            // Map wind speed to a bucket
            const scaledIndex = Math.floor(
              (Math.min(m, MAX_WIND_INTENSITY) / MAX_WIND_INTENSITY) *
                (colorStyles.length - 1)
            );
            buckets[scaledIndex].push(particle);
          }
        }
        particle.age += 1;
      }
    };

    const renderContext = this.canvas.getContext('2d');
    if (!renderContext) {
      console.error('Could not get canvas render context');
      return;
    }

    renderContext.lineWidth = PARTICLE_LINE_WIDTH;

    // Create an off-screen canvas for double buffering
    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = this.canvas.width;
    offscreenCanvas.height = this.canvas.height;
    const offscreenContext = offscreenCanvas.getContext('2d');

    if (!offscreenContext) {
      console.error('Could not get offscreen canvas context');
      return;
    }

    const draw = () => {
      // Check if offscreenCanvas and this.canvas are properly initialized
      if (!offscreenCanvas || !this.canvas) {
        console.error('Canvas not initialized');
        return;
      }

      // Clear the offscreen canvas
      offscreenContext.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height);

      // Draw existing content with reduced alpha
      offscreenContext.globalAlpha = 0.97; // Adjust this value to control the fade speed
      try {
        offscreenContext.drawImage(this.canvas, 0, 0);
      } catch (error) {
        console.error('Error drawing main canvas onto offscreen:', error);
        return;
      }

      // Reset for drawing new particles
      offscreenContext.globalAlpha = 1;

      // Draw new particle trails on the offscreen canvas
      for (const [index, bucket] of buckets.entries()) {
        if (bucket && bucket.length > 0) {
          offscreenContext.beginPath();
          offscreenContext.strokeStyle = colorStyles[index] || 'white'; // Fallback color
          offscreenContext.lineWidth = 1 + 0.25 * index;
          for (const particle of bucket) {
            if (
              Number.isNaN(particle.x) ||
              Number.isNaN(particle.y) ||
              Number.isNaN(particle.xt) ||
              Number.isNaN(particle.yt)
            ) {
              console.warn('Invalid particle coordinates:', particle);
              continue;
            }
            offscreenContext.moveTo(particle.x, particle.y);
            offscreenContext.lineTo(particle.xt, particle.yt);
            particle.x = particle.xt;
            particle.y = particle.yt;
          }
          offscreenContext.stroke();
        }
      }

      // Copy the offscreen canvas to the visible canvas
      renderContext.clearRect(0, 0, this.canvas.width, this.canvas.height);
      try {
        renderContext.drawImage(offscreenCanvas, 0, 0);
      } catch (error) {
        console.error('Error drawing offscreen canvas onto main canvas:', error);
      }
    };

    const frame = () => {
      if (!this.paused) {
        computeNextState();
        draw();
      }
      this.animationRequest = window.requestAnimationFrame(frame);
    };
    frame();
  }

  start(viewportBounds: number[][], width: number, height: number) {
    this.stop();
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
