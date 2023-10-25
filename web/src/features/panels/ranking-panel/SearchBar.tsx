import { HiMagnifyingGlass } from 'react-icons/hi2';

function SearchBar({ placeholder, searchHandler, value }: any) {
  const onHandleInput = (event: unknown) => {
    if (searchHandler) {
      searchHandler(event);
    }
  };

  return (
    <div className="mb-2 mr-[14px] flex h-11 flex-row items-center rounded border border-gray-400/10 bg-gray-100 p-3 transition hover:bg-gray-200/70 dark:border dark:border-gray-400/10 dark:bg-gray-800 dark:hover:bg-gray-700/70">
      <HiMagnifyingGlass />
      <input
        data-test-id="zone-search-bar"
        className="font h-8 w-full bg-transparent pl-2 text-base placeholder-gray-500 focus:border-b-2 focus:border-gray-300 focus:outline-none dark:focus:border-gray-600"
        placeholder={placeholder}
        onChange={onHandleInput}
        value={value}
      />
    </div>
  );
}

export default SearchBar;
