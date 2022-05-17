/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable react/jsx-no-target-blank */
// TODO: re-enable rules

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';

import { useTranslation } from '../../helpers/translation';
import ColorBlindCheckbox from '../../components/colorblindcheckbox';
import SocialButtons from './socialbuttons';

const Container = styled.div`
  @media (max-width: 767px) {
    display: none !important;
  }
`;

export default () => {
  const { __ } = useTranslation();
  const { search } = useLocation();

  return (
    <Container className="info-text">
      <ColorBlindCheckbox />
      <p>
        {__('panel-initial-text.thisproject')}{' '}
        <a href="https://github.com/tmrowco/electricitymap-contrib" target="_blank">
          {__('panel-initial-text.opensource')}
        </a>{' '}
        ({__('panel-initial-text.see')}{' '}
        <a href="https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md" target="_blank">
          {__('panel-initial-text.datasources')}
        </a>
        ).{' '}
        <span
          dangerouslySetInnerHTML={{
            __html: __(
              'panel-initial-text.contribute',
              'https://github.com/tmrowco/electricitymap-contrib/wiki/Getting-started'
            ),
          }}
        />
        .
      </p>
      <p>
        {__('footer.foundbugs')}{' '}
        <a href="https://github.com/tmrowco/electricitymap-contrib/issues/new" target="_blank">
          {__('footer.here')}
        </a>
        .<br />
      </p>
      <p>
        {__('footer.faq-text')}{' '}
        <Link to={{ pathname: '/faq', search }}>
          <span className="faq-link">{__('footer.faq')}</span>
        </Link>
      </p>
      <SocialButtons />
    </Container>
  );
};
