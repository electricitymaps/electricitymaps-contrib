import { useTranslation } from 'translation/translation';

export default function NoInformationMessage() {
  const { __ } = useTranslation();
  return (
    <div data-test-id="no-parser-message" className="pt-4 text-base">
      <span
        className="text-sm text-sky-600 no-underline hover:underline dark:invert"
        dangerouslySetInnerHTML={{
          __html: __(
            'country-panel.noParserInfo',
            'https://github.com/tmrowco/electricitymap-contrib/wiki/Getting-started'
          ),
        }}
      />
    </div>
  );
}
