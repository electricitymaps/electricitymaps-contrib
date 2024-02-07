import { twMerge } from 'tailwind-merge';

import { getShortenedZoneNameWithCountry } from '../translation/translation';
import { CountryFlag } from './Flag';

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
