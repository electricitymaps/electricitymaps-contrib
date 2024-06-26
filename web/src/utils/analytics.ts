type PlausibleEventProps = { readonly [propName: string]: string | number | boolean };
type PlausibleArguments = [string, { props: PlausibleEventProps }];

// TODO: Consider moving this to it's own global file
declare global {
  const plausible: {
    (...arguments: PlausibleArguments): void;
    q?: PlausibleArguments[];
  };

  interface Window {
    plausible?: typeof plausible | undefined;
  }
}
export default function trackEvent(
  eventId: string,
  additionalProps: PlausibleEventProps = {}
): void {
  if (import.meta.env.DEV) {
    console.log("not sending event to plausible because we're not in production");
    return;
  }
  window.plausible?.(eventId, { props: additionalProps });
}
