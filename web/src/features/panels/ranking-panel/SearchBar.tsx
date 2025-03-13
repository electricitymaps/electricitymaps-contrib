import { Search } from 'lucide-react';
import { memo, useCallback } from 'react';

function SearchBar({
  placeholder,
  searchHandler,
  value,
}: {
  placeholder?: string;
  searchHandler?: (inputEvent: React.ChangeEvent<HTMLInputElement>) => void;
  value: string;
}) {
  const onHandleInput = useCallback(
    (inputEvent: React.ChangeEvent<HTMLInputElement>) => {
      searchHandler?.(inputEvent);
    },
    [searchHandler]
  );

  return (
    <div className="mb-2 mr-[14px] flex h-11 flex-row items-center gap-3 rounded border border-neutral-400/10 bg-neutral-100 p-3 transition hover:bg-neutral-200/70 dark:border dark:border-neutral-400/10 dark:bg-neutral-800 dark:hover:bg-neutral-700/70">
      <Search />
      <input
        data-testid="zone-search-bar"
        className="font h-8 w-full bg-transparent text-sm placeholder-neutral-500 focus:border-b-2 focus:border-neutral-300 focus:outline-none dark:focus:border-neutral-600"
        placeholder={placeholder}
        onChange={onHandleInput}
        value={value}
      />
    </div>
  );
}

export default memo(SearchBar);
