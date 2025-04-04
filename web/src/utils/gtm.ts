import { Capacitor } from '@capacitor/core';

declare global {
  interface Window {
    dataLayer: unknown[];
  }
}

/**
 * Pushes an event to the Google Tag Manager dataLayer, but only if the
 * application is running in a standard web browser environment.
 * It checks if the Capacitor native platform is active and prevents pushing
 * data if it is.
 *
 * @param eventData - The event data object to push to the dataLayer.
 */
export const pushToDataLayer = (eventData: Record<string, unknown>): void => {
  // Ensure dataLayer exists
  window.dataLayer = window.dataLayer || [];
  // Check if the platform is native (Capacitor environment)
  const isNative = Capacitor.isNativePlatform();

  // Only push data if NOT running in a native Capacitor environment
  if (isNative) {
    // This block runs in the NATIVE environment
    // Optional: Log or handle the case where tracking is skipped in native
  } else {
    // This block runs in the WEB environment
    window.dataLayer.push(eventData);
  }
};
