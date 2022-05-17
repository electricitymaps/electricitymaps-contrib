import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import Icon from '../components/icon';

export default () => {
  const { __ } = useTranslation();
  const location = useLocation();

  const canRenderMap = useSelector((state) => state.application.webGLSupported);

  return (
    <div id="tab">
      <div id="tab-content">
        {canRenderMap && (
          <NavLink className="list-item" to={{ pathname: '/map', search: location.search }}>
            <img className="tab-icon-custom" src={resolvePath('images/electricitymap-icon.svg')} alt="" />
            <span className="tab-label">{__('mobile-main-menu.map')}</span>
          </NavLink>
        )}
        <NavLink className="list-item" to={{ pathname: '/ranking', search: location.search }}>
          <Icon iconName="view_list" />
          <span className="tab-label">{__('mobile-main-menu.areas')}</span>
        </NavLink>
        <NavLink className="list-item" to={{ pathname: '/info', search: location.search }}>
          <Icon iconName="info" />
          <span className="tab-label">{__('mobile-main-menu.about')}</span>
        </NavLink>
      </div>
    </div>
  );
};
