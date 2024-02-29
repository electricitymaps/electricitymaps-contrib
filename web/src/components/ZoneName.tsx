import { twMerge } from 'tailwind-merge';

import { getShortenedZoneNameWithCountry } from '../translation/translation';
import { CountryFlag } from './Flag';

export function ZoneName({
  zone,
  textStyle,
  zoneNameMaxLength,
}: {
  zone: string;
  textStyle?: string;
  zoneNameMaxLength?: number;
}) {
  return (
    <div className="flex items-center">
      <CountryFlag zoneId={zone} size={20} className="rounded-sm" />
      <p className={twMerge('truncate pl-1 text-base', textStyle)}>
        {getShortenedZoneNameWithCountry(zone, zoneNameMaxLength)}
      </p>
    </div>
  );
}
