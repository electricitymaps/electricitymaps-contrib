import { useTranslation } from 'react-i18next';

import { ZoneDataStatus } from './util';

const translations = {
  [ZoneDataStatus.NO_INFORMATION]: {
    name: 'country-panel.noParserInfo',
    object: {
      link: 'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Getting-started',
    },
  },
  [ZoneDataStatus.AGGREGATE_DISABLED]: {
    name: 'country-panel.aggregationDisabled',
    object: {},
  },
  [ZoneDataStatus.FULLY_DISABLED]: {
    name: 'country-panel.fullyDisabled',
    object: {
      link: 'https://github.com/electricitymaps/electricitymaps-contrib',
    },
  },
};

type PossibleStatusTypes =
  | ZoneDataStatus.NO_INFORMATION
  | ZoneDataStatus.AGGREGATE_DISABLED
  | ZoneDataStatus.FULLY_DISABLED;
export default function NoInformationMessage({ status }: { status: ZoneDataStatus }) {
  const { t } = useTranslation();

  const translationKey =
    translations[status as PossibleStatusTypes] ??
    translations[ZoneDataStatus.NO_INFORMATION];

  return (
    <div data-testid="no-parser-message" className="pt-4 text-center text-base">
      <span
        className="prose text-sm dark:prose-invert prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline"
        dangerouslySetInnerHTML={{
          __html: t(translationKey.name, translationKey.object),
        }}
      />
    </div>
  );
}
