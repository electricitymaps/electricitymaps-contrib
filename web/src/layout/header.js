import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { breakpoints } from '../scss/theme';

// TODO: Move all styles from styles.css to here
const Header = styled.div`
  background-color: transparent;
  z-index: 2;
  position: fixed;
  right: 0;
  top: 10px;
  color: ${props => props.theme.white};
  min-height: 50px; /* required for old Safari */

  &.brightmode {
    color: ${props => props.theme.black};
  }

  @media ${breakpoints.small} {
    display:none;
    min-height: 50px; /* required for old Safari */
    left: 0;
    top: 0;
    z-index: 2;
  }
`;

const Logo = styled.div`
  display: inline;
  font-family: ${props => props.theme['primary-font']};

  @media ${breakpoints.small} {
    margin-right: auto;
  }
`;

const Image = styled.div`
  vertical-align: text-top;
  display: inline-block;
  height: 21px;
  width: 139px;
  margin-right: 4px;
  margin-top:1.5px;
  background-image: ${props => props.brightmode ? 'url(../images/electricitymap-logo.svg)' 
  : 'url(../images/electricitymap-logo-white.svg)'};
  background-size: cover;
`;

const Maintitle = styled.span`
  transition: color 0.4s;
  color: ${props => props.brightmode ? props.theme.black : props.theme.white};
  @media ${breakpoints.small} {
    display: none !important;
  }
`;

// TODO: can this be Maintitle + one style to be more DRY
const Live = styled.span`
  transition: color 0.4s;
  color: ${props => props.brightmode ? props.theme.black : props.theme.white};
  font-weight: bold;
  @media ${breakpoints.small} {
    display: none !important;
  }
`;

const Anchor = styled.a`
  color: ${props => props.brightmode ? props.theme.black : props.theme.white};
  transition: color 0.4s;

  &:hover {
    color: #4178AC !important;
    text-decoration: none;
  }
`;

const mapStateToProps = state => ({
  brightModeEnabled: state.application.brightModeEnabled,
});

export default connect(mapStateToProps)(props => (
  <Header>
    <div id="header-content" className={props.brightModeEnabled ? 'brightmode' : null}>
      <Logo>
        <Image brightmode={ props.brightModeEnabled }/>
        <Maintitle brightmode={ props.brightModeEnabled }>
          <Live brightmode={ props.brightModeEnabled }>Live</Live>
          · <Anchor brightmode={ props.brightModeEnabled } href="https://api.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral">API</Anchor>
          · <Anchor brightmode={ props.brightModeEnabled } href="https://www.tmrow.com/blog/tags/electricitymap?utm_source=electricitymap.org&utm_medium=referral">Blog</Anchor>
        </Maintitle>
      </Logo>
    </div>
  </Header>
));
