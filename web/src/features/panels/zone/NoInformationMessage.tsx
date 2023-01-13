import { useTranslation } from 'translation/translation';

export default function NoInformationMessage() {
  const { __ } = useTranslation();
  return (
    <div data-test-id="no-parser-message" className="pt-4 text-center text-base">
      <span
        className="prose text-sm prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline dark:prose-invert"
        dangerouslySetInnerHTML={{
          __html: __(
            'country-panel.noParserInfo',
            'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Getting-started'
          ),
        }}
      />
    </div>
  );
}
