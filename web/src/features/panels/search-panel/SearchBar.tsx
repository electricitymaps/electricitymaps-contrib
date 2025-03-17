import { Search, X } from 'lucide-react';
import { memo, useCallback, useEffect, useRef, useState } from 'react';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

function SearchBar({
  placeholder,
  searchHandler,
  value,
}: {
  placeholder?: string;
  searchHandler?: (inputEvent: React.ChangeEvent<HTMLInputElement>) => void;
  value: string;
}) {
  const inputReference = useRef<HTMLInputElement>(null);
  const [inputValue, setInputValue] = useState(value);
  const debouncedValue = useDebounce(inputValue, 100);

  const onHandleInput = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    // Only update the input value, the search will be triggered by the debounced effect
    const newValue = inputEvent.target.value;
    setInputValue(newValue);
  }, []);

  useEffect(() => {
    if (searchHandler) {
      searchHandler({
        target: { value: debouncedValue },
      } as React.ChangeEvent<HTMLInputElement>);
    }
  }, [debouncedValue, searchHandler]);

  const handleClear = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setInputValue('');
  }, []);

  const handleContainerClick = useCallback(() => {
    inputReference?.current?.focus();
  }, [inputReference]);

  return (
    <div
      className="flex cursor-text flex-row items-center gap-2 px-3 py-2"
      onClick={handleContainerClick}
      role="button"
      tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          handleContainerClick();
        }
      }}
    >
      <Search className="size-6 text-neutral-500 dark:text-neutral-400" />
      <input
        ref={inputReference}
        data-testid="zone-search-bar"
        className="w-full border-0 bg-transparent placeholder-neutral-700 outline-none focus:outline-none dark:placeholder-neutral-300"
        placeholder={placeholder}
        onChange={onHandleInput}
        value={inputValue}
      />
      <div
        className={`transition-all duration-200 ${
          value ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      >
        <button
          onClick={handleClear}
          className="size-6 rounded-full p-1 text-neutral-500 transition-all hover:bg-neutral-300 focus-visible:outline-brand-green dark:text-neutral-400 dark:hover:bg-neutral-600 dark:focus-visible:bg-brand-green/10"
          data-testid="clear-search"
        >
          <X className="size-4" />
        </button>
      </div>
    </div>
  );
}

export default memo(SearchBar);
