import React from 'react';
import styled from 'styled-components';

import SharedHeader from '../components/sharedheader';
import OpenPositionsBadge from '../components/openpositionsbadge';

const logo = resolvePath('images/electricitymap-logo.svg');

const headerLinks = [
  {
    label: 'Live',
    active: true,
    id: 'live',
  },
  {
    label: (
      <React.Fragment>
        We&apos;re hiring!
        <OpenPositionsBadge />
      </React.Fragment>
    ),
    href: 'https://electricitymap.org/jobs#joboffers?utm_source=app.electricitymap.org&utm_medium=referral',
    id: 'jobs',
  },

  {
    label: 'Open Source',
    href: 'https://electricitymap.org/open-source?utm_source=app.electricitymap.org&utm_medium=referral',
    id: 'open-source',
  },
  {
    label: 'Blog',
    href: 'https://electricitymap.org/blog?utm_source=app.electricitymap.org&utm_medium=referral',
    id: 'blog',
  },
  {
    label: 'Get our data',
    href: 'https://electricitymap.org?utm_source=app.electricitymap.org&utm_medium=referral',
    id: 'get-data',
  },
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
