import { Capacitor } from '@capacitor/core';
import { EventName } from 'posthog-js';
import { usePostHog } from 'posthog-js/react';
import { useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { Charts, SpatialAggregate } from 'utils/constants';

export enum TrackEvents {
  MAP_CHART_SHARED = 'map_chart_shared',
  MAP_CONTRIBUTOR_AVATAR_PRESSED = 'map_contributor_avatar_pressed',
  MAP_CSV_LINK_PRESSED = 'map_csv_link_pressed',
  MAP_CTA_PRESSED = 'map_cta_pressed',
  MAP_FLOWTRACING_TOGGLED = 'map_flowTracing_toggled',
  MAP_METHODOLOGY_LINK_VISITED = 'map_methodology_link_visited',
  MAP_NAVIGATION_USED = 'map_navigation_used',
  MAP_SOCIAL_SHARE_PRESSED = 'map_social_share_pressed',
  MAP_SUPPORT_INITIATED = 'map_support_initiated',
  MAP_ZONEMODE_TOGGLED = 'map_zonemode_toggled',
}

export enum ShareType {
  DIRECT_LINK = 'direct_link',
  FACEBOOK = 'facebook',
  LINKEDIN = 'linkedin',
  REDDIT = 'reddit',
  SHARE = 'share',
  X = 'x',
}

type TrackEventFunction = (
  event: TrackEvents,
  properties?: Record<string, string>
) => void;

export function useTrackEvent() {
  const posthog = usePostHog();

  return useCallback(
    (event: TrackEvent, properties?: Record<string, string>) => {
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
      posthog?.capture(event as unknown as EventName, properties);
    },
    [posthog]
  );
}

export function useEvents(trackEvent: TrackEventFunction) {
  const { zoneId } = useParams<RouteParameters>();
  const zone = zoneId ?? 'map';

  return useMemo(() => ({
      // Other Links
      trackCsvLink: () => {
        trackEvent(TrackEvents.MAP_CSV_LINK_PRESSED, {
          zone,
        });
      },

      trackCtaMiddle: () => {
        trackEvent(TrackEvents.MAP_CTA_PRESSED, {
          type: 'middle',
          zone,
        });
      },

      trackCtaForecast: () => {
        trackEvent(TrackEvents.MAP_CTA_PRESSED, {
          type: 'forecast',
          zone,
        });
      },

      // Methodology links
      trackMissingDataMethodology: () =>
        trackEvent(TrackEvents.MAP_METHODOLOGY_LINK_VISITED, {
          link: 'missing-data',
        }),

      trackDataCollectionMethodology: () =>
        trackEvent(TrackEvents.MAP_METHODOLOGY_LINK_VISITED, {
          link: 'data-collection-and-processing-data',
        }),

      trackCarbonIntensityMethodology: () =>
        trackEvent(TrackEvents.MAP_METHODOLOGY_LINK_VISITED, {
          link: 'carbon-intensity-and-emission-factors',
        }),

      trackHistoricalAggregatesMethodology: () =>
        trackEvent(TrackEvents.MAP_METHODOLOGY_LINK_VISITED, {
          link: 'historical-aggregates',
        }),

      // Support
      trackSupportChat: () =>
        trackEvent(TrackEvents.MAP_SUPPORT_INITIATED, { type: 'chat' }),

      trackSupportFaq: () =>
        trackEvent(TrackEvents.MAP_SUPPORT_INITIATED, { type: 'faq' }),

      // Settings
      trackZoneMode: (type: SpatialAggregate) =>
        trackEvent(TrackEvents.MAP_ZONEMODE_TOGGLED, { type }),

      trackFlowTracing: (toggle_state: 'flowtracing_on' | 'flowtracing_off') =>
        trackEvent(TrackEvents.MAP_FLOWTRACING_TOGGLED, { toggle_state }),

      trackContributorAvatar: () =>
        trackEvent(TrackEvents.MAP_CONTRIBUTOR_AVATAR_PRESSED),
    }), [trackEvent, zone]);
}

export function useNavigationEvent(trackEvent: TrackEventFunction, link: string) {
  return useCallback(
    () => trackEvent(TrackEvents.MAP_NAVIGATION_USED, { link }),
    [trackEvent, link]
  );
}

export function useSocialShareEvents(trackEvent: TrackEventFunction, chart?: Charts) {
  const { zoneId } = useParams<RouteParameters>();
  const zone = zoneId ?? 'map';

  return useMemo(
    () => ({
      trackSocialShareDirectLink: () => {
        trackEvent(TrackEvents.MAP_SOCIAL_SHARE_PRESSED, {
          social: ShareType.DIRECT_LINK,
          zone,
          ...(chart ? { chart } : {}),
        });
      },

      trackSocialShareFacebook: () => {
        trackEvent(TrackEvents.MAP_SOCIAL_SHARE_PRESSED, {
          social: ShareType.FACEBOOK,
          zone,
          ...(chart ? { chart } : {}),
        });
      },

      trackSocialShareLinkedIn: () => {
        trackEvent(TrackEvents.MAP_SOCIAL_SHARE_PRESSED, {
          social: ShareType.LINKEDIN,
          zone,
          ...(chart ? { chart } : {}),
        });
      },

      trackSocialShareReddit: () => {
        trackEvent(TrackEvents.MAP_SOCIAL_SHARE_PRESSED, {
          social: ShareType.REDDIT,
          zone,
          ...(chart ? { chart } : {}),
        });
      },

      trackSocialShareX: () => {
        trackEvent(TrackEvents.MAP_SOCIAL_SHARE_PRESSED, {
          social: ShareType.X,
          zone,
          ...(chart ? { chart } : {}),
        });
      },
    }),
    [trackEvent, zone, chart]
  );
}
