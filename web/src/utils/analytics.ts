import posthog from 'posthog-js';
import { Charts, PHTrackEvent, TrackEvent } from 'utils/constants';

type PlausibleEventProps = { readonly [propName: string]: string | number | boolean };
type PlausibleArguments = [string, { props: PlausibleEventProps }];

// TODO: Consider moving this to its own global file
declare global {
  const plausible: {
    (...arguments_: PlausibleArguments): void; // Renamed 'arguments' to 'arguments_' to avoid conflict with the reserved keyword 'arguments'
    q?: PlausibleArguments[];
  };

  interface Window {
    plausible?: typeof plausible | undefined;
  }
}

export function trackEventPH(
  eventName: PHTrackEvent,
  additionalProps: PlausibleEventProps = {}
): void {
  if (import.meta.env.DEV) {
    // console.log("not sending event to posthog because we're not in production");
    // return;
  }
  console.log(eventName, additionalProps);
  posthog?.capture(eventName, additionalProps);
}

export default function trackEvent(
  eventId: TrackEvent,
  additionalProps: PlausibleEventProps = {}
): void {
  if (import.meta.env.DEV) {
    console.log("not sending event to plausible because we're not in production");
    return;
  }
  window.plausible?.(eventId, { props: additionalProps });
}

export enum ShareType {
  FACEBOOK = 'facebook',
  LINKEDIN = 'linkedin',
  TWITTER = 'twitter',
  BLUESKY = 'bluesky',
  REDDIT = 'reddit',
  COPY = 'copy',
  SHARE = 'share',
  COMPLETED_SHARE = 'completed_share',
}

export const trackShare =
  (shareType: ShareType, additionalProps = {}) =>
  () => {
    trackEventPH(PHTrackEvent.MAP_SOCIAL_SHARE_PRESSED, { social: shareType });
    trackEvent(TrackEvent.SHARE_BUTTON_CLICKED, { shareType, ...additionalProps });
  };

export const trackShareChart = (social: ShareType, chartId: Charts) => () => {
  posthog.capture(PHTrackEvent.MAP_CHART_SHARED, { social, chart_name: chartId });
};

// export const trackShareChart = (shareType: ShareType, chartId: Charts) => () =>
//   trackEvent(TrackEvent.SHARE_CHART, {
//     shareType,
//     chartId,
//   });

interface TrackChartSharesByShareType {
  [chartId: string]: {
    [shareType: string]: () => void;
  };
}

const trackChartShareByType: TrackChartSharesByShareType = Object.fromEntries(
  Object.values(Charts).map((chartId) => [
    chartId,
    Object.fromEntries(
      Object.values(ShareType).map((shareType) => [
        shareType,
        trackShareChart(shareType, chartId),
      ])
    ),
  ])
);

const trackByShareType: {
  [id: string]: {
    [shareType: string]: () => void;
  };
} = {
  ...trackChartShareByType,
  zone: Object.fromEntries(
    Object.values(ShareType).map((shareType) => [shareType, trackShare(shareType)])
  ),
};

export const getTrackByShareType = (id: Charts | 'zone') => trackByShareType[id];
