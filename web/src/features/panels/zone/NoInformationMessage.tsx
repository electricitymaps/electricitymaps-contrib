import { useTranslation } from 'react-i18next';

export default function NoInformationMessage() {
  const { t } = useTranslation();

  const translationName = 'country-panel.noParserInfo';
  const translationObject = {
    link: 'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Getting-started',
  };

  return (
    <div data-testid="no-parser-message" className="pt-4 text-center text-base">
      <span
        className="prose text-sm dark:prose-invert prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline"
        dangerouslySetInnerHTML={{ __html: t(translationName, translationObject) }}
      />
    </div>
  );
}
