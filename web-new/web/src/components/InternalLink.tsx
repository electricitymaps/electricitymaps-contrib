import { Link, LinkProps, useLocation } from 'react-router-dom';

export default function InternalLink({ to, ...rest }: LinkProps) {
  const location = useLocation();
  const toWithState = `${to}${location.search}${location.hash}`;
  return <Link to={toWithState} {...rest} />;
}
