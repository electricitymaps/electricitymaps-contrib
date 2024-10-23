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

  const [routeType, ...rest] = segments;

  if (routeType === 'zone') {
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

  if (routeType === 'map') {
    const [timeAverage, datetime] = rest;

    return {
      type: 'map',
      ...(timeAverage && { timeAverage: timeAverage as TimeAverage }),
      ...(datetime && { datetime }),
    };
  }

  return null;
}

export const hasPathTimeAverageAndDatetime = (path: string): boolean => {
  const parsedPath = parsePath(path);
  return parsedPath?.type === 'zone' && parsedPath?.timeAverage !== undefined;
};
