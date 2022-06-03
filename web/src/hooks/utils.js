import { useCallback, useState } from 'react';

/**
 * Hook to toggle a boolean value.
 * @param {boolean} initialState - Initial state of the toggle.
 * @returns {[boolean, function]} - Returns an array with the current state and a function to toggle it.
 * @example
 * const [isToggled, toggle] = useToggle(false);
 * Credit: https://usehooks.com/useToggle/
 */
export const useToggle = (initialState = false) => {
  // Initialize the state
  const [state, setState] = useState(initialState);

  // Define and memorize toggler function in case we pass down the component,
  // This function change the boolean value to it's opposite value
  const toggle = useCallback(() => setState((state) => !state), []);

  return [state, toggle];
};
