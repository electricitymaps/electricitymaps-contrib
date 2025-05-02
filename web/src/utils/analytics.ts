import { Capacitor } from '@capacitor/core';
import posthog from 'posthog-js';
import { Charts, TrackEvent } from 'utils/constants';

export function trackEvent(eventName: TrackEvent, additionalProps = {}): void {
  if (import.meta.env.DEV) {
    console.log("not sending event to posthog because we're not in production");
    return;
  }
  if (Capacitor.isNativePlatform()) {
    console.log('not sending event to posthog in native apps');
    return;
  }
  posthog?.capture(eventName, additionalProps);
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
    trackEvent(TrackEvent.MAP_SOCIAL_SHARE_PRESSED, { social: shareType });
  };

export const trackShareChart = (social: ShareType, chartId: Charts) => () => {
  posthog.capture(TrackEvent.MAP_CHART_SHARED, { social, chart_name: chartId });
};

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
