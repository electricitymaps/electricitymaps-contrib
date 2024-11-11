import { Link, LinkProps, useLocation, useParams } from 'react-router-dom';
import { RouteParameters } from 'types';

export default function InternalLink({ to, ...rest }: LinkProps) {
  const location = useLocation();
  const { urlTimeAverage } = useParams<RouteParameters>();
  const toWithState = `${to}${urlTimeAverage ? `/${urlTimeAverage}` : ''}${
    location.search
  }${location.hash}`;
  return <Link to={toWithState} {...rest} />;
}
