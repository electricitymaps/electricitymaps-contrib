import { Capacitor } from '@capacitor/core';

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

/**
 * @returns {Boolean} true if agent is probably a mobile device.
 */
export function isMobile() {
  return /android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i.test(
    navigator.userAgent
  );
}

/**
 * @returns {Boolean} true if agent is probably an iPhone.
 */
export function isIphone() {
  return (
    Capacitor.getPlatform() === 'ios' || /iPad|iPhone|iPod/.test(navigator.userAgent)
  );
}

/**
 * @returns {Boolean} true if agent is probably an Android.
 */
export function isAndroid() {
  return Capacitor.getPlatform() === 'android' || /Android/.test(navigator.userAgent);
}

export function isMobileWeb() {
  return Capacitor.getPlatform() === 'web' && (isIphone() || isAndroid() || isMobile());
}

export function isIos() {
  return /Mac/.test(navigator.userAgent) || isIphone();
}
