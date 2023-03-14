import flags from 'country-flag-icons/react/3x2';

const DEFAULT_FLAG_SIZE = 18;

function getCountryName(zoneId: string) {
  const flagName = zoneId.split('-')[0];
  return flagName.toUpperCase();
}

type HTMLSVGElement = HTMLElement & SVGElement;
interface CountryFlagProps
  extends React.HTMLAttributes<HTMLSVGElement>,
    React.SVGAttributes<HTMLSVGElement> {
  zoneId: string;
  size?: number;
}

export function CountryFlag({
  zoneId,
  size = DEFAULT_FLAG_SIZE,
  ...props
}: CountryFlagProps) {
  const countryName = getCountryName(zoneId) as keyof typeof flags;
  const FlagIcon = flags[countryName];

  if (!FlagIcon) {
    return <span className="h-[12px] w-[18px] bg-gray-400 text-[14px]"></span>;
  }
  return (
    <FlagIcon
      title="TODO"
      width={size}
      height={Math.floor((size / 3) * 2)}
      style={{
        minWidth: size,
      }}
      {...props}
    />
  );
}
