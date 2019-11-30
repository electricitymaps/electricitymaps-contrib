import React from 'react';

export default () => (
  <div id="header">
    <div id="header-content" className="brightmode">
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
);
