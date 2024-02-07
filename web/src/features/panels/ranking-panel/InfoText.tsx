import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'translation/translation';

function ExternalLink({ href, text }: { href: string; text: string }) {
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {text}
    </a>
  );
}

function FAQLink({ children }: { children: React.ReactNode }) {
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);
  return (
    <button
      className="text-sky-600 hover:underline dark:invert"
      onClick={() => {
        setIsFAQModalOpen(true);
      }}
    >
      {children}
    </button>
  );
}

export default function InfoText() {
  const { __ } = useTranslation();
  return (
    <div className="prose text-sm dark:prose-invert prose-p:my-1 prose-p:leading-snug prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline dark:prose-a:invert">
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
        {__('footer.faq-text')} <FAQLink>{__('footer.faq')}</FAQLink>
      </p>
    </div>
  );
}
