import { useVirtualizer } from '@tanstack/react-virtual';
import { CountryFlag } from 'components/Flag';
import InternalLink from 'components/InternalLink';
import { DataCenterIcon } from 'features/data-centers/DataCenterIcons';
import { useEffect, useRef } from 'react';
import { GridState } from 'types';

interface ZonelistProperties {
  data: SearchResultRowType[];
  selectedIndex: number;
}

export interface SearchResultRowType {
  key: string;
  flagZoneId?: keyof GridState; // will display a country flag
  dataCenterIconId?: string; // will display a data center icon
  displayName?: string;
  secondaryDisplayName?: string;
  englishDisplayName?: string;
  link: string;
}

function SearchResultRow({
  key,
  flagZoneId,
  dataCenterIconId,
  displayName,
  secondaryDisplayName,
  link,
  isSelected,
}: SearchResultRowType & { isSelected: boolean }) {
  return (
    <InternalLink
      className={`group flex h-11 w-full items-center gap-2 p-4 hover:bg-neutral-200/50 focus:outline-0 focus-visible:border-l-4 focus-visible:border-brand-green focus-visible:bg-brand-green/10 focus-visible:outline-0 dark:hover:bg-neutral-700/50 dark:focus-visible:bg-brand-green/10 ${
        isSelected ? 'bg-neutral-200/50 dark:bg-neutral-700/50' : ''
      }`}
      key={key}
      to={link}
      data-testid="zone-list-link"
    >
      {flagZoneId && (
        <CountryFlag
          zoneId={flagZoneId}
          size={18}
          className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
        />
      )}

      {dataCenterIconId && <DataCenterIcon provider={dataCenterIconId} />}

      <div className="flex min-w-0 grow flex-row items-center justify-between">
        <h3 className="min-w-0 truncate">{displayName}</h3>
        {secondaryDisplayName && (
          <span className="ml-2 shrink-0 truncate text-xs font-normal text-neutral-400 dark:text-neutral-400">
            {secondaryDisplayName}
          </span>
        )}
      </div>
    </InternalLink>
  );
}

export function VirtualizedSearchResultList({ data, selectedIndex }: ZonelistProperties) {
  const parentReference = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentReference.current,
    estimateSize: () => 44,
    overscan: 5,
  });

  const items = rowVirtualizer.getVirtualItems();

  // Use useEffect to handle scrolling when selection changes
  useEffect(() => {
    if (selectedIndex >= 0 && data.length > 0) {
      rowVirtualizer.scrollToIndex(selectedIndex, { align: 'auto' });
    }
  }, [selectedIndex, data.length, rowVirtualizer]);

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
              <SearchResultRow
                {...data[virtualRow.index]}
                isSelected={virtualRow.index === selectedIndex}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
