export function modifyDOM(ref, selector, callback) {
  if (ref && ref.current) {
    // This seems to be the most browser-compatible way to iterate through a list of nodes.
    // See: https://developer.mozilla.org/en-US/docs/Web/API/NodeList#Example.
    Array.prototype.forEach.call(ref.current.querySelectorAll(selector), callback);
  }
}
