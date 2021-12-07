import React from 'react';
import styled from 'styled-components';

import SharedHeader from '../components/sharedheader';

const logo = resolvePath('images/electricitymap-logo.svg');

const headerLinks = [
  {
    label: 'Live Map',
    active: true,
  },
  {
    label: 'Our Company',
    href: 'https://electricitymap.org/company?utm_source=app.electricitymap.org&utm_medium=referral',
  },
  {
    label: 'Open Source',
    href: 'https://electricitymap.org/open-source?utm_source=app.electricitymap.org&utm_medium=referral',
  },
  {
    label: 'Blog',
    href: 'https://electricitymap.org/blog?utm_source=app.electricitymap.org&utm_medium=referral',
  },
  {
    lable: 'Get Our Data',
    href: 'https://electricitymap.org/?utm_source=app.electricitymap.org&utm_medium=referral',
  },
  {
    label: 'Use our data',
    href: 'https://static.electricitymap.org/api/docs/index.html',
  },
  {
    label: 'Contribute to the OSP',
    href: 'https://github.com/electricityMap/electricitymap-contrib'
  }
];

const Container = styled.div`
  /* This makes sure the map and the other content doesn't
  go under the SharedHeader which has a fixed position. */
  height: 58px;
  @media (max-width: 767px) {
    display: none !important;
  }
`;

const Header = () => (
  <Container>
    <SharedHeader logo={logo} links={headerLinks} />
  </Container>
);

export default Header;
