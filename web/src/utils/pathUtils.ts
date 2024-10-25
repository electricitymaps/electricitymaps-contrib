import { isValidDate } from 'api/helpers';

import { TimeAverages } from './constants';

type TimeAverage = 'hourly' | 'daily' | 'monthly' | 'yearly';

type BaseRouteParameters = {
  timeAverage?: TimeAverage;
  datetime?: string;
};

type ZoneRouteResult = BaseRouteParameters & {
  type: 'zone';
  zoneId: string;
};

type MapRouteResult = BaseRouteParameters & {
  type: 'map';
};

type RouteResult = ZoneRouteResult | MapRouteResult | null;

export function parsePath(path: string): RouteResult {
  const segments = path.split('/').filter(Boolean);

  // Empty path or root
  if (segments.length === 0) {
    return { type: 'map' };
  }

  const [first, ...rest] = segments;

  // Handle direct datetime at root
  if (segments.length === 1) {
    if (isValidDate(first)) {
      return { type: 'map', datetime: first };
    }
    if (first === 'map') {
      return { type: 'map' };
    }
    return { type: 'map' };
  }

  // Handle zone paths
  if (first === 'zone') {
    if (rest.length === 0) {
      return null;
    }

    const [zoneId, timeAverage, datetime] = rest;

    if (rest.length === 1) {
      return {
        type: 'zone',
        zoneId,
      };
    }

    if (rest.length === 2) {
      if (!Object.values(TimeAverages).includes(timeAverage as TimeAverages)) {
        return { type: 'zone', zoneId };
      }
      return {
        type: 'zone',
        zoneId,
        timeAverage: timeAverage as TimeAverage,
      };
    }

    if (rest.length === 3) {
      if (!Object.values(TimeAverages).includes(timeAverage as TimeAverages)) {
        return { type: 'zone', zoneId };
      }
      return {
        type: 'zone',
        zoneId,
        timeAverage: timeAverage as TimeAverage,
        datetime,
      };
    }
  }

  // Handle map paths
  if (first === 'map') {
    if (rest.length === 0) {
      return { type: 'map' };
    }

    const [parameter1, parameter2] = rest;

    if (rest.length === 1) {
      if (Object.values(TimeAverages).includes(parameter1 as TimeAverages)) {
        return { type: 'map', timeAverage: parameter1 as TimeAverage };
      }
      if (isValidDate(parameter1)) {
        return { type: 'map', datetime: parameter1 };
      }

      return { type: 'map' };
    }

    if (rest.length === 2) {
      if (
        Object.values(TimeAverages).includes(parameter1 as TimeAverages) &&
        isValidDate(parameter2)
      ) {
        return {
          type: 'map',
          timeAverage: parameter1 as TimeAverage,
          datetime: parameter2,
        };
      }
      return { type: 'map' };
    }
  }

  return { type: 'map' };
}

export const hasPathDatetime = (path: string): boolean => {
  const result = parsePath(path);
  if (!result || !result.datetime) {
    return false;
  }
  return isValidDate(result.datetime);
};
