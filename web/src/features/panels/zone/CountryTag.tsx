import { CountryFlag } from 'components/Flag';
import { getCountryName } from 'translation/translation';

export function CountryTag({ zoneId, hideFlag }: { zoneId: string; hideFlag?: boolean }) {
  const countryName = getCountryName(zoneId);

  return (
    <span className="inline-flex h-5 items-center gap-1 rounded-full bg-gray-200 px-2 py-0.5 text-xs dark:bg-gray-900">
      {!hideFlag && <CountryFlag zoneId={zoneId} />}
      <span>{countryName}</span>
    </span>
  );
}
