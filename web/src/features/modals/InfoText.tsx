import { useTranslation } from 'react-i18next';

export default function InfoText() {
  const { t } = useTranslation();
  return (
    <div className="prose dark:prose-invert prose-p:my-1 prose-p:leading-snug prose-a:text-sky-600 hover:prose-a:underline">
      <p className="mb-4">{t('info.text')}</p>
      <p
        dangerouslySetInnerHTML={{
          __html: t('info.open-source-text', {
            link: 'https://github.com/electricitymaps/electricitymaps-contrib',
            sourcesLink:
              'https://github.com/electricitymaps/electricitymaps-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources',
          }),
        }}
      />
    </div>
  );
}
