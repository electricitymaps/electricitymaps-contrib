import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

// TODO: Move all styles from styles.css to here
const Wrapper = styled.div`
  background-color: transparent;
  z-index: 2;
  position: fixed;
  right: 0;
  top: 10px;
  color: #FFFFFF;
  min-height: 50px; /* required for old Safari */

  &.brightmode {
    color: #000000; /* TODO: define variable */
  }
`;

const mapStateToProps = state => ({
  brightModeEnabled: state.application.brightModeEnabled,
});

export default connect(mapStateToProps)(props => (
  <Wrapper>
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
  </Wrapper>
));
