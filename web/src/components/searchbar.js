import React, { useEffect, useRef } from 'react';
import { connect } from 'react-redux';
import { noop } from 'lodash';

const mapStateToProps = state => ({
  currentPage: state.application.currentPage,
});

const SearchBar = ({
  className,
  currentPage,
  documentKeyUpHandler,
  placeholder,
  searchHandler,
}) => {
  const ref = useRef(null);

  // Set up global key up handlers that apply to this search bar
  useEffect(() => {
    const keyUpHandler = documentKeyUpHandler
      ? ev => documentKeyUpHandler(ev.key, currentPage, ref)
      : noop;
    document.addEventListener('keyup', keyUpHandler);
    return () => {
      document.removeEventListener('keyup', keyUpHandler);
    };
  });

  // Apply the search query after every key press
  const handleKeyUp = (ev) => {
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

export default connect(mapStateToProps)(SearchBar);
