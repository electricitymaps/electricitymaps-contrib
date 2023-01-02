export default function trackEvent(
  eventId: string,
  additionalProps: { [key: string]: string | number | boolean } = {}
) {
  // @ts-ignore - plausible is defined in index.html
  window.plausible(eventId, { props: additionalProps });
}
