import { useVirtualizer } from '@tanstack/react-virtual';
import { CountryFlag } from 'components/Flag';
import InternalLink from 'components/InternalLink';
import { ChevronRight } from 'lucide-react';
import { useRef } from 'react';
import { GridState } from 'types';

interface ZonelistProperties {
  data: ZoneRowType[];
}

export interface ZoneRowType {
  zoneId: keyof GridState;
  ranking: number;
  color?: string;
  co2intensity?: number | null;
  countryName?: string;
  zoneName?: string;
  fullZoneName?: string;
}

function ZoneRow({ zoneId, color, ranking, countryName, zoneName }: ZoneRowType) {
  return (
    <InternalLink
      className="group my-1 flex h-11 w-full items-center gap-2 rounded bg-neutral-100 px-3 hover:bg-neutral-200 focus:border focus:border-neutral-400/60 focus-visible:outline-none dark:border dark:border-neutral-400/10 dark:bg-neutral-800 dark:hover:bg-neutral-700/70 dark:focus:border-neutral-500/80"
      key={ranking}
      to={`/zone/${zoneId}`}
      data-testid="zone-list-link"
    >
      <span className="flex w-4 justify-end text-xs">{ranking}</span>
      <div className="h-4 w-4 min-w-4 rounded-sm" style={{ backgroundColor: color }} />

      <CountryFlag size={30} zoneId={zoneId} />
      <div className="flex grow flex-col">
        <h3 className="truncate">{countryName || zoneName}</h3>
        {countryName && (
          <h4 className="truncate text-neutral-500 dark:text-neutral-400">{zoneName}</h4>
        )}
      </div>
      <ChevronRight
        size={14}
        className="hidden group-hover:block dark:text-neutral-400"
      />
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
              <ZoneRow key={virtualRow.index} {...data[virtualRow.index]} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
