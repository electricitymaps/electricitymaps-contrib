import { useMemo } from 'react';
import source from 'react-map-gl/dist/esm/components/source';
import { useTranslation } from 'translation/translation';
import { formatDataSources } from 'utils/formatting';
import zonesConfigJSON from '../../../../config/zones.json'; // Todo: improve how to handle json configs
import { getContributors } from './util';
const zonesConfig: Record<string, any> = zonesConfigJSON;

export function removeDuplicateSources(source: string | undefined) {
  if (!source) {
    return [''];
  }

  const sources = [
    ...new Set(
      source
        .split('","')
        .flatMap((x) =>
          x.split(',').map((x) => x.replaceAll('\\', '').replaceAll('"', ''))
        )
    ),
  ];

  return sources;
}

export default function Attribution({
  dataSources,
  zoneId,
}: {
  zoneId: string;
  dataSources?: string;
}) {
  const { __, i18n } = useTranslation();

  // TODO: Handle sources formatting in DBT or app-backend
  const formattedDataSources = useMemo(() => {
    return formatDataSources(removeDuplicateSources(dataSources), i18n.language);
  }, [dataSources, i18n.language]);

  return (
    <div className="message text-sm no-underline">
      <span>{__('country-panel.source')}:</span>
      <a
        style={{ textDecoration: 'none' }}
        href="https://github.com/electricitymaps/electricitymaps-contrib#data-sources/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources"
        target="_blank"
        rel="noreferrer"
      >
        {' '}
        <span className="hover:underline">{formattedDataSources || '?'}</span>
      </a>
      <small>
        {' '}
        (
        <span
          className="text-sm"
          style={{ textDecoration: 'none' }}
          dangerouslySetInnerHTML={{
            __html: __(
              'country-panel.addeditsource',
              'https://github.com/electricitymaps/electricitymaps-contrib#data-sources/tree/master/parsers'
            ),
          }}
        />
        )
      </small>
      {'  '}
      {__('country-panel.helpfrom')}
      <div className="flex flex-wrap gap-1">
        <ContributorList zoneId={zoneId} />
      </div>
    </div>
  );
}

function ContributorList({ zoneId }: { zoneId: string }) {
  const contributors = getContributors(zoneId);
  if (!contributors) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {contributors.map((contributor) => {
        return (
          <a
            key={contributor}
            href={`https://github.com/${contributor}`}
            rel="noopener noreferrer"
            target="_blank"
          >
            <img
              src={`https://avatars.githubusercontent.com/${contributor}?s=20`} // loads the avatar image at a default size of 20px
              srcSet={`https://avatars.githubusercontent.com/${contributor}?s=40 2x`} // loads the avatar image at a default size of 40px for high resolution displays
              alt={contributor}
              height="20"
              width="20"
              loading="lazy" // makes sure the image don't load until the user scrolls down
              className="rounded-sm"
            />
          </a>
        );
      })}
    </div>
  );
}
