import React from 'react';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import { NavLink, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import Icon from '../components/icon';

export default () => {
  const { __ } = useTranslation();
  const location = useLocation();

  const canRenderMap = useSelector((state) => (state as any).application.webGLSupported);

  return (
    <div id="tab">
      <div id="tab-content">
        {canRenderMap && (
          <NavLink className="list-item" to={{ pathname: '/map', search: location.search }}>
            {/* @ts-expect-error TS(2322): Type '{ iconName: string; }' is not assignable to ... Remove this comment to see the full error message */}
            <Icon iconName="electricitymaps" />
            <span className="tab-label">{__('mobile-main-menu.map')}</span>
          </NavLink>
        )}
        <NavLink className="list-item" to={{ pathname: '/ranking', search: location.search }}>
          {/* @ts-expect-error TS(2322): Type '{ iconName: string; }' is not assignable to ... Remove this comment to see the full error message */}
          <Icon iconName="view_list" />
          <span className="tab-label">{__('mobile-main-menu.areas')}</span>
        </NavLink>
        <NavLink className="list-item" to={{ pathname: '/info', search: location.search }}>
          {/* @ts-expect-error TS(2322): Type '{ iconName: string; }' is not assignable to ... Remove this comment to see the full error message */}
          <Icon iconName="info" />
          <span className="tab-label">{__('mobile-main-menu.about')}</span>
        </NavLink>
      </div>
    </div>
  );
};
