import { twMerge } from 'tailwind-merge';

import { getShortenedZoneNameWithCountry } from '../translation/translation';
import { CountryFlag } from './Flag';

export function ZoneName({ zone, textStyle }: { zone: string; textStyle?: string }) {
  return (
    <div className="flex items-center">
      <CountryFlag
        zoneId={zone}
        size={18}
        className="rounded-sm shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
      />
      <p className={twMerge('truncate pl-1 text-base', textStyle)}>
        {getShortenedZoneNameWithCountry(zone)}
      </p>
    </div>
  );
}
