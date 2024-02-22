import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
  return (
    <div className="prose text-sm dark:prose-invert prose-p:my-1 prose-p:leading-snug prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline dark:prose-a:invert">
      <p>
        {t('panel-initial-text.thisproject')}{' '}
        <ExternalLink
          href="https://github.com/electricitymaps/electricitymaps-contrib"
          text={t('panel-initial-text.opensource')}
        />{' '}
        ({t('panel-initial-text.see')}{' '}
        <ExternalLink
          href="https://github.com/electricitymaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md"
          text={t('panel-initial-text.datasources')}
        />
        ).{' '}
        <span
          dangerouslySetInnerHTML={{
            __html: t('panel-initial-text.contribute', {
              link: 'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Getting-started',
            }),
          }}
        />
        .
      </p>
      <p>
        {t('footer.foundbugs')}{' '}
        <ExternalLink
          href="https://github.com/electricitymaps/electricitymaps-contrib/issues/new"
          text={t('footer.here')}
        />
        .
      </p>
      <p>
        {t('footer.faq-text')} <FAQLink>{t('footer.faq')}</FAQLink>
      </p>
    </div>
  );
}
