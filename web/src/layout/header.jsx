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
    href: 'https://electricitymaps.com/jobs/#joboffers?utm_source=app.electricitymaps.com&utm_medium=referral',
    id: 'jobs',
  },

  {
    label: 'Open Source',
    href: 'https://electricitymaps.com/open-source/?utm_source=app.electricitymaps.com&utm_medium=referral',
    id: 'open-source',
  },
  {
    label: 'Blog',
    href: 'https://electricitymaps.com/blog/?utm_source=app.electricitymaps.com&utm_medium=referral',
    id: 'blog',
  },
  {
    label: 'Get our data',
    href: 'https://electricitymaps.com?utm_source=app.electricitymaps.com&utm_medium=referral',
    id: 'get-data',
  },
];

const Container = styled.div`
  /* This makes sure the map and the other content doesn't
  go under the SharedHeader which has a fixed position. */
  height: 58px;

  // Provides extra space for Ipad
  padding-top: 0px;
  padding-top: constant(safe-area-inset-top, 0px);
  padding-top: env(safe-area-inset-top, 0px);

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
