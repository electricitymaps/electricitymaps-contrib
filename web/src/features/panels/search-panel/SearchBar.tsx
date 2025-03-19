import { Search, X } from 'lucide-react';
import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

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
  selectedIndex,
  onSelectedIndexChange,
  totalResults,
}: {
  placeholder?: string;
  searchHandler?: (inputEvent: React.ChangeEvent<HTMLInputElement>) => void;
  value: string;
  selectedIndex: number;
  onSelectedIndexChange: (index: number) => void;
  totalResults: number;
}) {
  const inputReference = useRef<HTMLInputElement>(null);
  const [inputValue, setInputValue] = useState(value);
  const debouncedValue = useDebounce(inputValue, 100);
  const navigate = useNavigate();

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

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowDown': {
          event.preventDefault();
          onSelectedIndexChange(
            selectedIndex >= totalResults - 1 ? 0 : selectedIndex + 1
          );
          break;
        }
        case 'ArrowUp': {
          event.preventDefault();
          onSelectedIndexChange(
            selectedIndex <= 0 ? totalResults - 1 : selectedIndex - 1
          );
          break;
        }
        case 'Enter': {
          event.preventDefault();
          if (selectedIndex >= 0 && totalResults > 0) {
            // Find the selected zone link and navigate to it
            const selectedLink = document.querySelector(
              `[data-index="${selectedIndex}"] a[data-testid="zone-list-link"]`
            ) as HTMLAnchorElement;
            if (selectedLink) {
              navigate(selectedLink.pathname);
            }
          }
          break;
        }
        default: {
          if (event.key === 'Enter') {
            handleContainerClick();
          }
        }
      }
    },
    [selectedIndex, totalResults, onSelectedIndexChange, navigate, handleContainerClick]
  );

  return (
    <div
      className="flex cursor-text flex-row items-center gap-2 px-3 py-2"
      onClick={handleContainerClick}
      role="button"
      tabIndex={-1}
      onKeyDown={handleKeyDown}
    >
      <Search className="size-6 text-neutral-500 dark:text-neutral-400" />
      <input
        ref={inputReference}
        data-testid="zone-search-bar"
        className="w-full border-0 bg-transparent placeholder-neutral-700 outline-none focus:outline-none dark:placeholder-neutral-300"
        placeholder={placeholder}
        onChange={onHandleInput}
        value={inputValue}
        onKeyDown={handleKeyDown}
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
