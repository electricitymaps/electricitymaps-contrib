import { CountryFlag } from '../components/Flag';
import { getShortenedZoneNameWithCountry } from '../translation/translation';
import { twMerge } from 'tailwind-merge';

export function ZoneName({ zone, textStyle }: { zone: string; textStyle?: string }) {
  return (
    <div className="flex items-center">
      <CountryFlag zoneId={zone} />
      <p className={twMerge('truncate pl-1 text-base', textStyle)}>
        {getShortenedZoneNameWithCountry(zone)}
      </p>
    </div>
  );
}
