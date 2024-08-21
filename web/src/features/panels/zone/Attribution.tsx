import { GithubButton } from 'components/buttons/GithubButton';
import { useTranslation } from 'react-i18next';

import { getContributors } from './util';

export default function Attribution({ zoneId }: { zoneId: string }) {
  const { t } = useTranslation();
  const { zoneContributorsIndexArray, contributors } = getContributors(zoneId);

  return (
    <div className="flex flex-col gap-3 pt-1.5">
      {zoneContributorsIndexArray.length > 0 && (
        <div className="flex flex-row justify-between">
          <div className="text-sm font-semibold">{t('country-panel.helpfrom')}</div>
          <ContributorList
            zoneContributorsIndexArray={zoneContributorsIndexArray}
            contributors={contributors}
          />
        </div>
      )}
      <GithubButton />
    </div>
  );
}

function ContributorList({
  zoneContributorsIndexArray,
  contributors,
}: {
  zoneContributorsIndexArray: number[];
  contributors: string[];
}) {
  if (!zoneContributorsIndexArray) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {zoneContributorsIndexArray.map((contributorIndex) => (
        <a
          key={contributors.at(contributorIndex)}
          href={`https://github.com/${contributors.at(contributorIndex)}`}
          rel="noopener noreferrer"
          target="_blank"
        >
          <img
            src={`https://avatars.githubusercontent.com/${contributors.at(
              contributorIndex
            )}?s=20`} // loads the avatar image at a default size of 20px
            srcSet={`https://avatars.githubusercontent.com/${contributors.at(
              contributorIndex
            )}?s=40 2x`} // loads the avatar image at a default size of 40px for high resolution displays
            alt={contributors.at(contributorIndex)}
            height="20"
            width="20"
            loading="lazy" // makes sure the image don't load until the user scrolls down
            className="rounded-full"
          />
        </a>
      ))}
    </div>
  );
}
