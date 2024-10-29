import { Charts, TrackEvent } from 'utils/constants';

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
  REDDIT = 'reddit',
  COPY = 'copy',
  SHARE = 'share',
}

export const trackShare = (shareType: ShareType) => () =>
  trackEvent(TrackEvent.SHARE_BUTTON_CLICKED, { shareType });

export const trackShareChart = (shareType: ShareType, chartId: Charts) => () =>
  trackEvent(TrackEvent.SHARE_CHART, {
    shareType,
    chartId,
  });

interface TrackChartSharesByShareType {
  [chartId: string]: {
    [shareType: string]: () => void;
  };
}

const makeTrackChartShareFunctions = () => {
  const trackChartShareByType: TrackChartSharesByShareType = {};

  for (const chartId of Object.values(Charts)) {
    for (const shareType of Object.values(ShareType)) {
      if (!(chartId in trackChartShareByType)) {
        trackChartShareByType[chartId] = {};
      }
      trackChartShareByType[chartId][shareType] = trackShareChart(shareType, chartId);
    }
  }

  return trackChartShareByType;
};

const trackChartShareByType: TrackChartSharesByShareType = makeTrackChartShareFunctions();

export const getTrackChartShares = (chartId: Charts) => trackChartShareByType[chartId];
