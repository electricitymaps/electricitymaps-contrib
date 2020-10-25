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

const mapStateToProps = state => ({
  brightModeEnabled: state.application.brightModeEnabled,
});

export default connect(mapStateToProps)(props => (
  <Header>
    <div id="header-content" className={props.brightModeEnabled ? 'brightmode' : null}>
      <div className="logo">
        <div className="image" id="electricitymap-logo" />
        <span className="maintitle small-screen-hidden">
          <span className="live" style={{ fontWeight: 'bold' }}>Live</span>
          · <a href="https://api.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral">API</a>
          · <a href="https://www.tmrow.com/blog/tags/electricitymap?utm_source=electricitymap.org&utm_medium=referral">Blog</a>
        </span>
      </div>
    </div>
  </Header>
));
