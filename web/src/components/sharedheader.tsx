import React, { useState } from 'react';
import styled, { css } from 'styled-components';
import { useTrackEvent } from '../hooks/tracking';

const Wrapper = styled.header`
  align-items: center;
  background: white;
  // Shadow only towards bottom to allow having space above header
  box-shadow: 0 4px 6px -2px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  color: black;
  display: flex;
  font-family: 'Euclid Triangle', 'Open Sans', sans-serif;
  font-size: 15px;
  height: 58px;
  justify-content: space-between;
  min-height: 58px; /* required for old Safari */
  padding: 0 48px 0 25px;
  position: fixed;
  transition: background-color 0.5s;
  width: 100vw;
  z-index: 3;

  @media (max-width: 850px) {
    // provides some extra space for the logo on smaller screens
    padding-right: 12px;
  }

  ${(props) =>
    (props as any).collapsed &&
    `
    padding: 0 24px;
  `};

  ${(props) =>
    (props as any).inverted &&
    `
    background: transparent;
    color: white;
    box-shadow: none;

    img {
      filter: invert(100%);
    }

    a:after {
      background: white;
    }
  `};
`;

const Logo = styled.img`
  height: 48px;
  margin-top: 3px;
`;

const linkUnderline = css`
  &:after {
    background: #62b252;
    bottom: 0;
    content: '';
    display: block;
    left: 0;
    position: absolute;
    height: 2px;
    width: 100%;
  }
`;

const Link = styled.a`
  color: inherit;
  display: inline-block;
  line-height: 34px;
  padding: 12px 16px;
  position: relative;
  text-decoration: none;
  width: fit-content;

  &:hover {
    color: inherit;
    text-decoration: none;
    text-shadow: 0.5px 0 0 currentColor;
  }

  ${(props) =>
    (props as any).active &&
    `
    text-shadow: 0.5px 0 0 currentColor;
    ${linkUnderline}
  `}
`;

const MenuDrawerBackground = styled.div`
  background: black;
  display: none;
  opacity: 0.3;
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;

  ${(props) =>
    (props as any).visible &&
    `
    display: block;
  `};
`;

const MenuDrawerContent = styled.div`
  align-items: center;
  background: white;
  color: black;
  display: flex;
  flex-direction: column;
  text-align: center;
  font-size: 125%;
  padding-bottom: 16px;
  position: absolute;
  top: 0;
  left: 0;
  transform: translateY(-100%);
  transition: transform 0.3s ease-in-out;
  width: 100vw;
  z-index: 1;

  ${(props) =>
    (props as any).visible &&
    `
    transform: translateY(0);
  `};
`;

const MenuButton = ({ onClick }: any) => (
  <svg viewBox="0 0 100 80" width="48" height="48" onClick={onClick} style={{ cursor: 'pointer', padding: '8px 12px' }}>
    <rect width="100" height="10" fill="currentColor" />
    <rect y="30" width="100" height="10" fill="currentColor" />
    <rect y="60" width="100" height="10" fill="currentColor" />
  </svg>
);

const ResponsiveMenu = ({ children, collapsed }: any) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);
  const openMenu = () => setMenuOpen(true);

  // Show hamburger menu on smaller screens
  return collapsed ? (
    <>
      <MenuButton onClick={openMenu} />
      {/* @ts-expect-error TS(2769): No overload matches this call. */}
      <MenuDrawerBackground visible={menuOpen} onClick={closeMenu} />
      {/* @ts-expect-error TS(2769): No overload matches this call. */}
      <MenuDrawerContent visible={menuOpen} onClick={closeMenu}>
        {children}
      </MenuDrawerContent>
    </>
  ) : (
    <div>{children}</div>
  );
};

const SharedHeader = ({ collapsed = false, inverted = false, links = [], logo }: any) => {
  const trackEvent = useTrackEvent();

  return (
    // @ts-expect-error TS(2769): No overload matches this call.
    <Wrapper inverted={inverted} collapsed={collapsed}>
      <a href="https://app.electricitymaps.com/map">
        <Logo src={logo} alt="logo" />
      </a>
      <ResponsiveMenu collapsed={collapsed}>
        {/* @ts-expect-error TS(7031): Binding element 'label' implicitly has an 'any' ty... Remove this comment to see the full error message */}
        {links.map(({ label, href, active, id }) => (
          // @ts-expect-error TS(2769): No overload matches this call.
          <Link key={id} href={href} active={active} onClick={() => trackEvent('HeaderLink Clicked', { linkId: id })}>
            {label}
          </Link>
        ))}
      </ResponsiveMenu>
    </Wrapper>
  );
};

export default SharedHeader;
