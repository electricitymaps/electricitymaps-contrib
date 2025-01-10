import { TIME_RANGE_TO_TIME_AVERAGE } from 'api/helpers';
import { Link, LinkProps, useLocation, useParams } from 'react-router-dom';
import { RouteParameters } from 'types';

export default function InternalLink({ to, ...rest }: LinkProps) {
  const location = useLocation();

  const { urlTimeRange } = useParams<RouteParameters>();
  const toWithState = `${to}${
    urlTimeRange ? `/${TIME_RANGE_TO_TIME_AVERAGE[urlTimeRange]}/${urlTimeRange}` : ''
  }${location.search}${location.hash}`;
  return <Link to={toWithState} {...rest} />;
}
