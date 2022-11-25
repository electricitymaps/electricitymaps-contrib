import InternalLink from 'components/InternalLink';
import type { ReactElement } from 'react';
import { HiChevronRight } from 'react-icons/hi2';
import { GridState } from 'types';
import { CountryTag } from '../zone/CountryTag';

interface ZonelistProperties {
  data: ZoneRowType[];
}

export interface ZoneRowType {
  zoneId: keyof GridState;
  ranking?: number;
  color?: string;
  co2intensity?: number;
  countryName?: string;
  zoneName?: string;
}

function ZoneRow({ zoneId, color, ranking, countryName, zoneName }: ZoneRowType) {
  return (
    <InternalLink
      className="group my-1 flex h-9 w-full items-center overflow-hidden rounded bg-gray-100 pl-3  text-left hover:bg-gray-200 dark:bg-gray-700"
      key={ranking}
      to={`/zone/${zoneId}`}
    >
      <p className=" flex w-4 justify-end pr-2 text-sm">{ranking}</p>
      <div
        className="mr-2 h-4 w-4 min-w-[16px] rounded"
        style={{ backgroundColor: color }}
      ></div>
      <CountryTag zoneId={zoneId} />
      <div className="flex flex-grow items-center justify-between overflow-hidden">
        <div className="flex  flex-col justify-center overflow-hidden px-2 ">
          <p className="truncate text-sm leading-none">{countryName}</p>
          <p
            className={`${
              countryName ? 'truncate text-xs text-gray-400' : 'truncate text-sm '
            }`}
          >
            {zoneName}
          </p>
        </div>
        <div className="min-w-2">
          <p className="hidden pr-2 group-hover:block">
            <HiChevronRight />
          </p>
        </div>
      </div>
    </InternalLink>
  );
}

export default function Zonelist(properties: ZonelistProperties): ReactElement {
  return (
    <div>
      {properties.data.map((rowProps, index) => {
        return <ZoneRow key={index} {...rowProps} ranking={index + 1} />;
      })}
    </div>
  );
}
