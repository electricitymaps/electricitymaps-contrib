import React from 'react';
import styled from 'styled-components';
import { useSelector } from 'react-redux';

import SharedHeader from '../components/sharedheader';

const logoBlack = resolvePath('images/electricitymap-logo.svg');
const logoWhite = resolvePath('images/electricitymap-logo-white.svg');

const headerLinks = [
  {
    label: 'Live',
    active: true,
  },
  {
    label: 'Open Source',
    href: 'https://api.electricitymap.org/open-source?utm_source=electricitymap.org&utm_medium=referral',
  },
  {
    label: 'Blog',
    href: 'https://www.tmrow.com/blog/tags/electricitymap?utm_source=electricitymap.org&utm_medium=referral',
  },
  {
    label: 'API',
    href: 'https://api.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral',
  },
];

const Container = styled.div`
  /* This makes sure the map and the other content doesn't
  go under the SharedHeader which has a fixed position. */
  height: 58px;
`;

const Header = () => {
  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);
  const logo = brightModeEnabled ? logoBlack : logoWhite;

  return (
    <Container className="small-screen-hidden">
      <SharedHeader logo={logo} links={headerLinks} />
    </Container>
  );
};

export default Header;
