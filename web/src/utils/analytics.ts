import { Capacitor } from '@capacitor/core';
import posthog from 'posthog-js';
import { Charts, TrackEvent } from 'utils/constants';

export function trackEvent(eventName: TrackEvent, additionalProps = {}): void {
  if (import.meta.env.DEV) {
    console.log("not sending event to posthog because we're not in production");
    return;
  }
  if (Capacitor.isNativePlatform()) {
    // not sending event to posthog from native apps
    return;
  }

  posthog?.capture(eventName, additionalProps);
}

export enum ShareType {
  DIRECT_LINK = 'direct_link',
  FACEBOOK = 'facebook',
  LINKEDIN = 'linkedin',
  REDDIT = 'reddit',
  SHARE = 'share',
  X = 'x',
}

export const trackShare = (shareType: ShareType) => (zone: string) => {
  trackEvent(TrackEvent.MAP_SOCIAL_SHARE_PRESSED, { social: shareType, zone });
};

export const trackShareChart = (social: ShareType, chartId: Charts) => (zone: string) => {
  trackEvent(TrackEvent.MAP_CHART_SHARED, { social, chart_name: chartId, zone });
};

interface TrackChartSharesByShareType {
  [chartId: string]: {
    [shareType: string]: (zone: string) => void;
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
    [shareType: string]: (zone: string) => void;
  };
} = {
  ...trackChartShareByType,
  zone: Object.fromEntries(
    Object.values(ShareType).map((shareType) => [shareType, trackShare(shareType)])
  ),
};

export const getTrackByShareType = (id: Charts | 'zone') => trackByShareType[id];
