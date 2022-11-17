import React from 'react';
import { Link, useLocation } from 'react-router-dom';

import { useTranslation } from '../../../translation/translation';
// Import ColorBlindCheckbox from '../../components/colorblindcheckbox';
// Import SocialButtons from './socialbuttons';

const Container = styled.div`
  @media (max-width: 767px) {
    display: none !important;
  }

  p {
    margin: 0.4rem 0;
    line-height: 1.2rem;
  }
`;

export default function () {
  const { __ } = useTranslation();
  const { search } = useLocation();

  return (
    <Container className="info-text">
      <ColorBlindCheckbox />
      <p>
        {__('panel-initial-text.thisproject')}{' '}
        <a
          href="https://github.com/electricitymaps/electricitymaps-contrib"
          target="_blank"
          rel="noreferrer"
        >
          {__('panel-initial-text.opensource')}
        </a>{' '}
        ({__('panel-initial-text.see')}{' '}
        <a
          href="https://github.com/electricitymaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md"
          target="_blank"
          rel="noreferrer"
        >
          {__('panel-initial-text.datasources')}
        </a>
        ).{' '}
        <span
          dangerouslySetInnerHTML={{
            __html: __(
              'panel-initial-text.contribute',
              'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Getting-started'
            ),
          }}
        />
        .
      </p>
      <p>
        {__('footer.foundbugs')}{' '}
        <a
          href="https://github.com/electricitymaps/electricitymaps-contrib/issues/new"
          target="_blank"
          rel="noreferrer"
        >
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
}
