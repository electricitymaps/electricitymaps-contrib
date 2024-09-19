import flags from 'country-flag-icons/react/3x2';
import { getCountryName } from 'translation/translation';

const DEFAULT_FLAG_SIZE = 18;

function getCountryCode(zoneId: string) {
  const flagName = zoneId.split('-')[0];
  return flagName.toUpperCase();
}

interface CountryFlagProps {
  zoneId: string;
  size?: number;
  className?: string;
}

export function CountryFlag({
  zoneId,
  size = DEFAULT_FLAG_SIZE,
  className,
}: CountryFlagProps) {
  const countryCode = getCountryCode(zoneId) as keyof typeof flags;
  const FlagIcon = flags[countryCode];
  const countryName = getCountryName(zoneId);

  if (!FlagIcon) {
    return <span className="h-[12px] w-[18px] bg-gray-400 text-[14px]"></span>;
  }
  return (
    <FlagIcon
      title={countryName}
      width={size}
      height={Math.floor((size / 3) * 2)}
      style={{
        minWidth: size,
      }}
      className={className}
    />
  );
}
