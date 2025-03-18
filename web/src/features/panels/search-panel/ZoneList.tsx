import { useVirtualizer } from '@tanstack/react-virtual';
import { CountryFlag } from 'components/Flag';
import InternalLink from 'components/InternalLink';
import { useRef } from 'react';
import { GridState } from 'types';

interface ZonelistProperties {
  data: ZoneRowType[];
}

export interface ZoneRowType {
  zoneId: keyof GridState;
  countryName?: string;
  zoneName?: string;
  fullZoneName?: string;
  displayName?: string;
  seoZoneName?: string;
  englishZoneName?: string;
}

function ZoneRow({ zoneId, countryName, zoneName }: ZoneRowType) {
  return (
    <InternalLink
      className="group flex h-11 w-full items-center gap-2 p-4 hover:bg-neutral-200/50 focus:outline-0 focus-visible:border-l-4 focus-visible:border-brand-green focus-visible:bg-brand-green/10 focus-visible:outline-0  dark:hover:bg-neutral-700/50 dark:focus-visible:bg-brand-green/10"
      key={zoneId}
      to={`/zone/${zoneId}`}
      data-testid="zone-list-link"
    >
      <CountryFlag
        zoneId={zoneId}
        size={18}
        className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
      />

      <div className="flex min-w-0 grow flex-row items-center justify-between">
        <h3 className="min-w-0 truncate">{zoneName}</h3>
        {countryName && (
          <span className="ml-2 shrink-0 truncate text-xs font-normal text-neutral-400 dark:text-neutral-400">
            {countryName}
          </span>
        )}
      </div>
    </InternalLink>
  );
}

export function VirtualizedZoneList({ data }: ZonelistProperties) {
  const parentReference = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentReference.current,
    estimateSize: () => 44,
    overscan: 5,
  });

  const items = rowVirtualizer.getVirtualItems();

  return (
    // This should show exactly 6 and a half rows
    <div ref={parentReference} className="h-full max-h-72 w-full overflow-y-auto">
      <div
        className="transition-all"
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
