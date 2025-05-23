import { useVirtualizer } from '@tanstack/react-virtual';
import { useEffect, useRef } from 'react';

import { SearchResultType } from './getSearchData';
import SearchResultRow from './SearchResultRow';

interface SearchResultListProps {
  data: SearchResultType[];
  selectedIndex: number;
}

export default function SearchResultList({ data, selectedIndex }: SearchResultListProps) {
  const parentReference = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentReference.current,
    estimateSize: () => 44, // Height of each row
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
                key={virtualRow.index}
                result={data[virtualRow.index]}
                isSelected={virtualRow.index === selectedIndex}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
