import { ForecastEntry, GfsForecastResponse } from 'api/getWeatherData';

import { bilinearInterpolateVector } from './calc';
import { floorModulus, isValue } from './util';

/**
 * Builds the grid of wind vectors
 */
export default class Grid {
  lo1 = 0;
  la1 = 90;
  dx = 1;
  dy = 1;
  nx = 360;
  ny = 181;

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
    const header = uComp?.header || vComp?.header;

    if (header) {
      (this.lo1 = header.lo1), (this.la1 = header.la1); // the grid's origin (e.g., 0.0E, 90.0N)
      (this.dx = header.dx), (this.dy = header.dy); // distance between grid points (e.g., 2.5 deg lon, 2.5 deg lat)
      (this.nx = header.nx), (this.ny = header.ny); // number of grid points W-E and N-S (e.g., 144 x 73)
    }

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
