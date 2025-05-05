import { Capacitor } from '@capacitor/core';
import { PostHog } from 'posthog-js';
import { Charts, TrackEvent } from 'utils/constants';

export function trackEvent(
  posthog: PostHog,
  eventName: TrackEvent,
  additionalProps = {}
): void {
  if (import.meta.env.DEV) {
    console.log("not sending event to posthog because we're not in production");
    return;
  }

  // if user did not accept cookies, then posthog was not initialized and we don't want to send events
  if (!posthog || !posthog.capture) {
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

// TODO: clean up track share logic

export const trackShare = (shareType: ShareType) => (posthog: PostHog, zone: string) => {
  trackEvent(posthog, TrackEvent.MAP_SOCIAL_SHARE_PRESSED, { social: shareType, zone });
};

export const trackShareChart =
  (social: ShareType, chartId: Charts) => (posthog: PostHog, zone: string) => {
    trackEvent(posthog, TrackEvent.MAP_CHART_SHARED, {
      social,
      chart_name: chartId,
      zone,
    });
  };

interface TrackChartSharesByShareType {
  [chartId: string]: {
    [shareType: string]: (posthog: PostHog, zone: string) => void;
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
    [shareType: string]: (posthog: PostHog, zone: string) => void;
  };
} = {
  ...trackChartShareByType,
  zone: Object.fromEntries(
    Object.values(ShareType).map((shareType) => [shareType, trackShare(shareType)])
  ),
};

export const getTrackByShareType = (id: Charts | 'zone') => trackByShareType[id];
