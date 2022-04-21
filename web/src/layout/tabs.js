import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { useTranslation } from '../helpers/translation';

export default () => {
  const { __ } = useTranslation();
  const location = useLocation();

  const canRenderMap = useSelector(state => state.application.webGLSupported);

  return (
    <div id="tab">
      <div id="tab-content">
        {canRenderMap && (
          <NavLink
            className="list-item"
            to={{ pathname: '/map', search: location.search }}
          >
            <img className="tab-icon-custom" src={resolvePath('images/electricitymap-icon.svg')} alt="" />
            <span className="tab-label">{__('mobile-main-menu.map')}</span>
          </NavLink>
        )}
        <NavLink
          className="list-item"
          to={{ pathname: '/ranking', search: location.search }}
        >
          <svg>
            <use href="/images/material-icon-sprite.svg#view_list" />
          </svg>
          <span className="tab-label">{__('mobile-main-menu.areas')}</span>
        </NavLink>
        <NavLink
          className="list-item"
          to={{ pathname: '/info', search: location.search }}
        >
          <svg>
            <use href="/images/material-icon-sprite.svg#info" />
          </svg>
          <span className="tab-label">{__('mobile-main-menu.about')}</span>
        </NavLink>
      </div>
    </div>
  );
};
