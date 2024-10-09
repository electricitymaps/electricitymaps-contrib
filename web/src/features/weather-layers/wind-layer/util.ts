/**
 * @returns {Boolean} true if the specified value is not null and not undefined.
 */
export function isValue(x: unknown) {
  return x !== null && x !== undefined;
}

/**
 * @returns {Number} returns remainder of floored division, i.e., floor(a / n). Useful for consistent modulo
 * of negative numbers. See http://en.wikipedia.org/wiki/Modulo_operation.
 */
export function floorModulus(a: number, n: number) {
  return a - n * Math.floor(a / n);
}
