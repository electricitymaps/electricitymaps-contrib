import { WindVector } from './calc';
import { Bounds, NULL_WIND_VECTOR, Particle } from './windy';

/**
 * Helper class for calculating particle movement
 */
export default class Field {
  columns: WindVector[][];
  bounds: Bounds;

  constructor(columns: WindVector[][], bounds: Bounds) {
    this.columns = columns;
    this.bounds = bounds;
  }

  /**
   * @returns {Array} wind vector [u, v, magnitude] at the point (x, y), or NaN vector if undefined
   */
  getWind(x: number, y: number): WindVector {
    const column = this.columns[Math.round(x)];
    return column?.[Math.round(y)] || NULL_WIND_VECTOR;
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
