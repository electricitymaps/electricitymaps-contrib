import { useVirtualizer } from '@tanstack/react-virtual';
import { CountryFlag } from 'components/Flag';
import InternalLink from 'components/InternalLink';
import { useRef } from 'react';
import { HiChevronRight } from 'react-icons/hi2';
import { GridState } from 'types';

interface ZonelistProperties {
  data: ZoneRowType[];
}

export interface ZoneRowType {
  zoneId: keyof GridState;
  ranking?: number;
  color?: string;
  co2intensity?: number | null;
  countryName?: string;
  zoneName?: string;
}

function ZoneRow({ zoneId, color, ranking, countryName, zoneName }: ZoneRowType) {
  return (
    <InternalLink
      className="group my-1 flex h-11 w-full items-center overflow-hidden rounded bg-gray-100 pl-3 text-left transition hover:bg-gray-200 focus:border focus:border-gray-400/60 focus-visible:outline-none dark:border dark:border-gray-400/10 dark:bg-gray-800 dark:hover:bg-gray-700/70 dark:focus:border-gray-500/80"
      key={ranking}
      to={`/zone/${zoneId}`}
      data-test-id="zone-list-link"
    >
      <p className=" flex w-4 justify-end pr-2 text-xs">{ranking}</p>
      <div
        className="mr-2 h-4 w-4 min-w-[16px] rounded-sm	"
        style={{ backgroundColor: color }}
      ></div>

      <CountryFlag size={30} zoneId={zoneId} />
      <div className="flex grow items-center justify-between overflow-hidden">
        <div className="flex  flex-col content-center justify-center overflow-hidden px-2 pt-1">
          <p className="truncate font-poppins text-sm  leading-none">{countryName}</p>
          <p
            className={`${
              countryName
                ? 'truncate font-poppins text-xs text-gray-500 dark:text-gray-400'
                : 'truncate font-poppins text-sm '
            }`}
          >
            {zoneName}
          </p>
        </div>
        <p className="hidden min-w-2 pr-2 group-hover:block dark:text-gray-400">
          <HiChevronRight />
        </p>
      </div>
    </InternalLink>
  );
}

export function VirtualizedZoneList({ data }: ZonelistProperties) {
  const parentReference = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentReference.current,
    estimateSize: () => 48,
    overscan: 5,
  });

  const items = rowVirtualizer.getVirtualItems();

  return (
    <div ref={parentReference} className="h-full w-full overflow-y-auto">
      <div
        style={{
          height: rowVirtualizer.getTotalSize(),
          width: '100%',
          position: 'relative',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            transform: `translateY(${items[0]?.start ?? 0}px)`,
          }}
        >
          {items.map((virtualRow) => (
            <div key={virtualRow.key} data-index={virtualRow.index}>
              <ZoneRow
                key={virtualRow.index}
                {...data[virtualRow.index]}
                ranking={virtualRow.index + 1}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
