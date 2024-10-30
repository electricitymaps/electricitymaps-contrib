import { Link, LinkProps, useLocation, useParams } from 'react-router-dom';

export default function InternalLink({ to, ...rest }: LinkProps) {
  const location = useLocation();
  const { urlTimeAverage } = useParams();
  const toWithState = `${to}${urlTimeAverage ? `/${urlTimeAverage}` : ''}${
    location.search
  }${location.hash}`;
  return <Link to={toWithState} {...rest} />;
}
