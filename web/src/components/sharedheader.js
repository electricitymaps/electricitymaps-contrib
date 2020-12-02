import React, { useState } from 'react';
import styled from 'styled-components';

const Wrapper = styled.header`
  align-items: center;
  background: white;
  box-shadow: 0 0 6px 1px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  color: black;
  display: flex;
  font-size: 16px;
  height: 66px;
  justify-content: space-between;
  min-height: 66px; /* required for old Safari */
  padding: 0 8px 0 32px;
  position: fixed;
  transition: background-color 0.5s;
  width: 100vw;
  z-index: 3;

  ${props => props.inverted && `
    background: transparent;
    color: white;
    box-shadow: none;

    img {
      filter: invert(100%);
    }
  `};
`;

const Logo = styled.img`
  height: 24px;
`;

const Link = styled.a`
  color: inherit;
  display: inline-block;
  padding: 12px 16px;
  text-decoration: none;

  &:hover {
    color: inherit;
    text-decoration: none;
    text-shadow: 0.5px 0 0 currentColor;
  }

  ${props => props.active && `
    text-shadow: 0.5px 0 0 currentColor;
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

  ${props => props.visible && `
    display: block;
  `};
`;

const MenuDrawerContent = styled.div`
  background: white;
  color: black;
  display: flex;
  flex-direction: column;
  text-align: center;
  font-size: 125%;
  position: absolute;
  top: 0;
  left: 0;
  transform: translateY(-100%);
  transition: transform 0.3s ease-in-out;
  width: 100vw;
  z-index: 1;

  ${props => props.visible && `
    transform: translateY(0);
  `};
`;

const MenuButton = ({ onClick }) => (
  <svg
    viewBox="0 0 100 80"
    width="40"
    height="40"
    onClick={onClick}
    style={{ cursor: 'pointer', height: 20, padding: '8px 12px' }}
  >
    <rect width="100" height="10" />
    <rect y="30" width="100" height="10" />
    <rect y="60" width="100" height="10" />
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

const SharedHeader = ({
  collapsed = false,
  inverted = false,
  links = [],
  logo,
  style,
}) => (
  <Wrapper style={style} inverted={inverted}>
    <Logo src={logo} alt="logo" />
    <ResponsiveMenu collapsed={collapsed}>
      {links.map(({ label, href, active }) => (
        <Link key={label} href={href} active={active}>
          {label}
        </Link>
      ))}
    </ResponsiveMenu>
  </Wrapper>
);

export default SharedHeader;
