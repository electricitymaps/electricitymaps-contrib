import { CountryFlag } from 'components/Flag';

// TODO: move to translations when config is added
const getCountryName = (zoneId: string) => {
  if (zoneId === 'DK-DK1') {
    return 'Denmark';
  }
  if (zoneId === 'ES') {
    return 'Spain';
  }
  return 'USA';
};

export function CountryTag({ zoneId }: { zoneId: string }) {
  const countryName = getCountryName(zoneId);
  // eslint-disable-next-line @typescript-eslint/no-magic-numbers
  const isACountry = zoneId !== 'US' && zoneId.length === 2; // TODO: set up proper method to check if zoneId is a country

  if (isACountry) {
    return <CountryFlag zoneId={zoneId} flagSize={16} className="inline-flex" />;
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-200 px-2 py-0.5 text-xs dark:bg-gray-900">
      <CountryFlag zoneId={zoneId} flagSize={16} />
      <span>{countryName}</span>
    </span>
  );
}
