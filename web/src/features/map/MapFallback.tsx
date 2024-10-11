export function isOldIOSVersion() {
  const userAgent = window.navigator.userAgent;
  const isIos = userAgent.includes('iPhone') || userAgent.includes('iPad');
  const iosVersion = userAgent.match(/OS [1-9]{1,2}_\d(_\d)?/)?.[0].replace('OS ', '');

  // Attempt to detect if this in in Google Chrome Dev Tools, where the responsive dev tools
  // have version 13.2 by default
  const isDevelopmentTools = window.navigator?.vendor === 'Google Inc.';

  // If version is less than 14.7 Maplibre won't work
  const lowestSupportedVersion = '14_7';

  return (
    isIos && !isDevelopmentTools && iosVersion && iosVersion < lowestSupportedVersion
  );
}

export default function MapFallback() {
  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center p-4 text-center">
      <h1 className="text-xl font-bold">Unsupported iOS version</h1>
      <p className="mt-4">
        This app is unfortunately not supported on devices running iOS 14.6 or older.
      </p>
    </div>
  );
}
