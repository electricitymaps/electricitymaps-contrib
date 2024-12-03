import { Search } from 'lucide-react';
import { useCallback } from 'react';

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
    <div className="mb-2 mr-[14px] flex h-11 flex-row items-center gap-3 rounded border border-gray-400/10 bg-gray-100 p-3 transition hover:bg-gray-200/70 dark:border dark:border-gray-400/10 dark:bg-gray-800 dark:hover:bg-gray-700/70">
      <Search />
      <input
        data-testid="zone-search-bar"
        className="font h-8 w-full bg-transparent text-base placeholder-gray-500 focus:border-b-2 focus:border-gray-300 focus:outline-none dark:focus:border-gray-600"
        placeholder={placeholder}
        onChange={onHandleInput}
        value={value}
      />
    </div>
  );
}

export default SearchBar;
