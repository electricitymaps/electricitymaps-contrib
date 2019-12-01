import React from 'react';
import { connect } from 'react-redux';

// TODO: Move all styles from styles.css to here

const mapStateToProps = state => ({
  brightModeEnabled: state.application.brightModeEnabled,
});

export default connect(mapStateToProps)(props => (
  <div id="header">
    <div id="header-content" className={props.brightModeEnabled ? 'brightmode' : null}>
      <div className="logo">
        <div className="image" id="electricitymap-logo" />
        <span className="maintitle small-screen-hidden">
          <span className="live" style={{ fontWeight: 'bold' }}>Live</span>
          · <a href="https://api.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral">API</a>
          · <a href="https://medium.com/electricitymap?utm_source=electricitymap.org&utm_medium=referral">Blog</a>
        </span>
      </div>
    </div>
  </div>
));
