import { getCountryName } from 'translation/translation';

export function CountryTag({ zoneId }: { zoneId: string; size?: number }) {
  const countryName = getCountryName(zoneId);

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-200 px-2 py-0.5 text-xs dark:bg-gray-900">
      <span>{countryName}</span>
    </span>
  );
}
