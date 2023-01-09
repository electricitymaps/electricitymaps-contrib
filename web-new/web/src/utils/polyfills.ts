/**
 * Polyfills Array.at() for older versions of Safari
 * Source: https://github.com/tc39/proposal-relative-indexing-method#polyfill
 */
export function polyfillArrayAt() {
  if (![].at) {
    Array.prototype.at = function (n) {
      console.log('Running .at with', n);
      // ToInteger() abstract op
      n = Math.trunc(n) || 0;
      // Allow negative indexing from the end
      if (n < 0) {
        n += this.length;
      }
      // OOB access is guaranteed to return undefined
      if (n < 0 || n >= this.length) {
        return undefined;
      }
      // Otherwise, this is just normal property access
      return this[n];
    };
  }
}

// Initialise all polyfills
polyfillArrayAt();
