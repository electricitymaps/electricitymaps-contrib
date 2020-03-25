/* eslint-disable jsx-a11y/anchor-is-valid */
import React from 'react';

// Modules
import { __ } from '../helpers/translation';

export default () => (
  <div id="tab">
    <div id="tab-content">
      <a className="list-item map-button">
        <img className="tab-icon-custom" src="/images/electricitymap-icon.svg" alt="" />
        <span className="tab-label">{__('mobile-main-menu.map')}</span>
      </a>
      <a className="list-item highscore-button">
        <i className="material-icons" aria-hidden="true">view_list</i>
        <span className="tab-label">{__('mobile-main-menu.areas')}</span>
      </a>
      <a className="list-item info-button">
        <i className="material-icons" aria-hidden="true">info</i>
        <span className="tab-label">{__('mobile-main-menu.about')}</span>
      </a>
    </div>
  </div>
);
