import React, { useState } from 'react';
import styled, { css } from 'styled-components';
import { useTrackEvent } from '../hooks/tracking';

const Wrapper = styled.header`
  align-items: center;
  background: white;
  box-shadow: 0 0 6px 1px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  color: black;
  display: flex;
  font-family: 'Euclid Triangle', 'Open Sans', sans-serif;
  font-size: 15px;
  height: 58px;
  justify-content: space-between;
  min-height: 58px; /* required for old Safari */
  padding: 0 48px 0 32px;
  position: fixed;
  transition: background-color 0.5s;
  width: 100vw;
  z-index: 3;

  ${(props) =>
    props.collapsed &&
    `
    padding: 0 24px;
  `};

  ${(props) =>
    props.inverted &&
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
  height: 24px;
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
    props.active &&
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
    props.visible &&
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
    props.visible &&
    `
    transform: translateY(0);
  `};
`;

const MenuButton = ({ onClick }) => (
  <svg viewBox="0 0 100 80" width="48" height="48" onClick={onClick} style={{ cursor: 'pointer', padding: '8px 12px' }}>
    <rect width="100" height="10" fill="currentColor" />
    <rect y="30" width="100" height="10" fill="currentColor" />
    <rect y="60" width="100" height="10" fill="currentColor" />
  </svg>
);

const ResponsiveMenu = ({ children, collapsed }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);
  const openMenu = () => setMenuOpen(true);

  // Show hamburger menu on smaller screens
  return collapsed ? (
    <>
      <MenuButton onClick={openMenu} />
      <MenuDrawerBackground visible={menuOpen} onClick={closeMenu} />
      <MenuDrawerContent visible={menuOpen} onClick={closeMenu}>
        {children}
      </MenuDrawerContent>
    </>
  ) : (
    <div>{children}</div>
  );
};

const SharedHeader = ({ collapsed = false, inverted = false, links = [], logo }) => {
  const trackEvent = useTrackEvent();

  return (
    <Wrapper inverted={inverted} collapsed={collapsed}>
      <a href="https://app.electricitymap.org/map">
        <Logo src={logo} alt="logo" />
      </a>
      <ResponsiveMenu collapsed={collapsed}>
        {links.map(({ label, href, active, id }) => (
          <Link key={id} href={href} active={active} onClick={() => trackEvent('HeaderLink Clicked', { linkId: id })}>
            {label}
          </Link>
        ))}
      </ResponsiveMenu>
    </Wrapper>
  );
};

export default SharedHeader;
