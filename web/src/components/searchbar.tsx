import React, { useEffect, useRef } from 'react';
import { noop } from '../helpers/noop';

const SearchBar = ({ className, documentKeyUpHandler, placeholder, searchHandler }: any) => {
  const ref = useRef(null);

  // Set up global key up handlers that apply to this search bar
  useEffect(() => {
    const keyUpHandler = documentKeyUpHandler ? (ev: any) => documentKeyUpHandler(ev.key, ref) : noop;
    document.addEventListener('keyup', keyUpHandler);
    return () => {
      document.removeEventListener('keyup', keyUpHandler);
    };
  });

  // Apply the search query after every key press
  const handleKeyUp = (ev: any) => {
    if (searchHandler) {
      searchHandler(ev.target.value.toLowerCase());
    }
  };

  return (
    <div className={className}>
      <input ref={ref} placeholder={placeholder} onKeyUp={handleKeyUp} />
    </div>
  );
};

export default SearchBar;
