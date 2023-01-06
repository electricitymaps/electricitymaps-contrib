import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { useTranslation } from '../helpers/translation';
import Icon from '../components/icon';
import styled from 'styled-components';

const Tab = styled.div`
  position: relative;
  background-color: $lighter-gray;
  fill-opacity: 0.5;
  box-shadow: 0px 0px 12px 0px rgba(0, 0, 0, 0.1);
  z-index: 2;
  flex: 0 0 auto;

  @include respond-to('medium-up') {
    display: none;
  }
`;

const TabContent = styled.div`
  display: flex;
  height: 56px;

  .list-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    text-align: center;
    flex-direction: column;
    width: 50%;
    font-size: 12px;
    padding-bottom: 10px;
    padding-top: 8px;
    font-family: $primary-font;
    transition: padding-top 0.4s;
    font-family: $headline-font;

    &.active {
      color: black;
      font-size: 14px;
      fill-opacity: 1;
      padding-top: 6px;
    }
  }

  a {
    color: rgba(0, 0, 0, 0.5);

    .tab-label {
      font-size: 12px;
    }

    &:hover {
      color: $black;
      text-decoration: none;
    }
  }

  i {
    font-size: 24px;
  }
`;

export default () => {
  const { __ } = useTranslation();
  const location = useLocation();

  const canRenderMap = useSelector((state) => state.application.webGLSupported);

  return (
    <Tab>
      <TabContent>
        {canRenderMap && (
          <NavLink className="list-item" to={{ pathname: '/map', search: location.search }}>
            <Icon iconName="electricitymaps" />
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
      </TabContent>
    </Tab>
  );
};
