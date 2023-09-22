import { useTranslation } from 'translation/translation';
import { ZoneDataStatus } from './util';

const translations = {
  [ZoneDataStatus.NO_INFORMATION]: {
    name: 'country-panel.noParserInfo',
    args: [
      'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Getting-started',
    ],
  },
  [ZoneDataStatus.AGGREGATE_DISABLED]: {
    name: 'country-panel.aggregationDisabled',
    args: [],
  },
};

type PossibleStatusTypes =
  | ZoneDataStatus.NO_INFORMATION
  | ZoneDataStatus.AGGREGATE_DISABLED;
export default function NoInformationMessage({ status }: { status: ZoneDataStatus }) {
  const { __ } = useTranslation();

  const translationKey =
    translations[status as PossibleStatusTypes] ??
    translations[ZoneDataStatus.NO_INFORMATION];

  return (
    <div data-test-id="no-parser-message" className="pt-4 text-center text-base">
      <span
        className="prose text-sm dark:prose-invert prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline"
        dangerouslySetInnerHTML={{
          __html: __(translationKey.name, ...translationKey.args),
        }}
      />
    </div>
  );
}
