import { isValidDate } from 'api/helpers';

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

  if (segments.length === 0) {
    return null;
  }

  const [firstSegment, ...rest] = segments;

  // If it's a single segment that looks like a date, return as map with datetime
  if (segments.length === 1 && isValidDate(firstSegment)) {
    return {
      type: 'map',
      datetime: firstSegment,
    };
  }

  if (firstSegment === 'zone') {
    const [zoneId, timeAverage, datetime] = rest;
    if (!zoneId) {
      return null;
    }

    return {
      type: 'zone',
      zoneId,
      ...(timeAverage && { timeAverage: timeAverage as TimeAverage }),
      ...(datetime && { datetime }),
    };
  }

  if (firstSegment === 'map') {
    const [parameter1, parameter2] = rest;

    if (parameter1 && isValidDate(parameter1)) {
      return {
        type: 'map',
        datetime: parameter1,
      };
    }

    return {
      type: 'map',
      ...(parameter1 && { timeAverage: parameter1 as TimeAverage }),
      ...(parameter2 && { datetime: parameter2 }),
    };
  }

  return null;
}

export const hasPathDatetime = (path: string): boolean => {
  const parsedPath = parsePath(path);
  if (!parsedPath?.datetime) {
    return false;
  }
  return isValidDate(parsedPath.datetime);
};
