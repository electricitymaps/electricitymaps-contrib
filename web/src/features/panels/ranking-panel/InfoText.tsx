import { Link } from 'react-router-dom';

import { useTranslation } from 'translation/translation';
import { createToWithState } from 'utils/helpers';

function ExternalLink({ href, text }: { href: string; text: string }) {
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {text}
    </a>
  );
}

export default function InfoText() {
  const { __ } = useTranslation();
  return (
    <div className="prose text-sm prose-p:my-1 prose-p:leading-snug prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline dark:prose-invert">
      <p>
        {__('panel-initial-text.thisproject')}{' '}
        <ExternalLink
          href="https://github.com/electricitymaps/electricitymaps-contrib"
          text={__('panel-initial-text.opensource')}
        />{' '}
        ({__('panel-initial-text.see')}{' '}
        <ExternalLink
          href="https://github.com/electricitymaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md"
          text={__('panel-initial-text.datasources')}
        />
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
        <ExternalLink
          href="https://github.com/electricitymaps/electricitymaps-contrib/issues/new"
          text={__('footer.here')}
        />
        .
      </p>
      <p>
        {__('footer.faq-text')}{' '}
        <Link to={createToWithState('/faq')}>
          <span data-test-id="faq-link">{__('footer.faq')}</span>
        </Link>
      </p>
    </div>
  );
}
