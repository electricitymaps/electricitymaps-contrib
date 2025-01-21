import { Capacitor } from '@capacitor/core';

const IOS_DEVICE_PATTERN: RegExp = /iPad|iPhone|iPod/;
const MOBILE_DEVICE_PATTERN: RegExp =
  /android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i;
const ANDROID_DEVICE_PATTERN: RegExp = /android/i;
const MAC_DEVICE_PATTERN: RegExp = /Mac/;

/**
 * @returns {Boolean} true if the specified value is not null and not undefined.
 */
export const isValue = (x: unknown) => x !== null && x !== undefined;

/**
 * @returns {Number} returns remainder of floored division, i.e., floor(a / n). Useful for consistent modulo
 * of negative numbers. See http://en.wikipedia.org/wiki/Modulo_operation.
 */
export const floorModulus = (a: number, n: number) => a - n * Math.floor(a / n);

/**
 * @returns {Boolean} true if agent is probably a mobile device.
 */
export const isMobile = () => MOBILE_DEVICE_PATTERN.test(navigator.userAgent);

/**
 * @returns {Boolean} true if agent is probably an iPhone.
 */
export const isIphone = () =>
  Capacitor.getPlatform() === 'ios' || IOS_DEVICE_PATTERN.test(navigator.userAgent);

/**
 * @returns {Boolean} true if agent is probably an Android.
 */
export const isAndroid = () =>
  Capacitor.getPlatform() === 'android' ||
  ANDROID_DEVICE_PATTERN.test(navigator.userAgent);

export const isMobileWeb = () =>
  Capacitor.getPlatform() === 'web' && (isIphone() || isAndroid() || isMobile());

export const isIos = () => MAC_DEVICE_PATTERN.test(navigator.userAgent) || isIphone();
