// u, v, m
export type WindVector = [number, number, number];

/**
 * interpolation for vectors like wind (u,v,m)
 * @returns {WindVector}
 */
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
 * @returns {[number, number]} uses map projection and returns needed value
 */
const project = (map: maplibregl.Map, lat: number, lon: number) => {
  // both in radians, use deg2rad if necessary
  const projected = map.project([lon, lat]);
  return [projected.x, projected.y];
};

/**
 * Calculate distortion of the wind vector caused by the shape of the projection at point (x, y). The wind
 * vector is modified in place and returned by this function.
 * @returns {WindVector}
 */
export const distort = (
  map: maplibregl.Map,
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

const distortion = (map: maplibregl.Map, λ: number, φ: number, x: number, y: number) => {
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
 * @returns {Bounds} puts boundary info into one object
 */
export const buildBounds = (bounds: number[][], width: number, height: number) => {
  const upperLeft = bounds[0];
  const lowerRight = bounds[1];
  const x = Math.round(upperLeft[0]);
  const y = Math.max(Math.floor(upperLeft[1]), 0);
  const yMax = Math.min(Math.ceil(lowerRight[1]), height - 1);
  return { x: x, y: y, yMax: yMax, width: width, height: height };
};
