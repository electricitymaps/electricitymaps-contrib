'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.isInitialOrHasNoParents = isInitialOrHasNoParents;
exports.isInvalidOrder = isInvalidOrder;
exports.getOrder = getOrder;
exports.getLoaderObject = getLoaderObject;
exports.mergeOptions = mergeOptions;
exports.isString = isString;
exports.isFunction = isFunction;
exports.isType = isType;
/* eslint-disable
  no-param-reassign
*/
function isInitialOrHasNoParents(chunk) {
  let parentCount = 0;

  for (const chunkGroup of chunk.groupsIterable) {
    parentCount += chunkGroup.getNumberOfParents();
  }

  return chunk.isOnlyInitial() || parentCount === 0;
}

function isInvalidOrder(a, b) {
  // Async chunks' modules don't get turned into ExtractedModule
  // instances for some reason. This is a temporary fix that
  // moves the isInvalidOrder check inside a condition.
  if (a.getPrevModules && b.getPrevModules) {
    const bBeforeA = a.getPrevModules().indexOf(b) >= 0;
    const aBeforeB = b.getPrevModules().indexOf(a) >= 0;

    return aBeforeB && bBeforeA;
  }

  return false;
}

function getOrder(a, b) {
  // Async chunks' modules don't get turned into ExtractedModule
  // instances for some reason. This is a temporary fix that
  // moves the custom sorting logic inside a condition.
  if (a.getOriginalModule && b.getOriginalModule) {
    const aOrder = a.getOrder();
    const bOrder = b.getOrder();
    if (aOrder < bOrder) return -1;
    if (aOrder > bOrder) return 1;

    // We are trying to use the underlying index2 property
    // of the original module, but this property seems
    // to be set to null most of the time. It makes
    // sorting with it pointless. We should look
    // into saving the index, index2 and depth
    // props (maybe inside ExtractedModule).
    const aIndex = a.getOriginalModule().index2;
    const bIndex = b.getOriginalModule().index2;
    if (aIndex < bIndex) return -1;
    if (aIndex > bIndex) return 1;

    const bBeforeA = a.getPrevModules().indexOf(b) >= 0;
    const aBeforeB = b.getPrevModules().indexOf(a) >= 0;
    if (aBeforeB && !bBeforeA) return -1;
    if (!aBeforeB && bBeforeA) return 1;

    // Sorting by id is the default behavior of webpack
    // and it keeps the modules in the correct order,
    // except for async imports. That's the reason
    // it is inside the conditional branch
    if (a.id < b.id) return -1;
    if (a.id > b.id) return 1;
  }

  // Sorting by identifier breaks the order of async imported
  // modules either because webpack sorts them by default,
  // or because they are processed in the correct order
  // in the first place, or maybe because the modules
  // aren't ExtractedModule instances in this case.
  // Returning 0 keeps the already correct order.
  /*
  const ai = a.identifier();
  const bi = b.identifier();
  if (ai < bi) return -1;
  if (ai > bi) return 1;
  */

  return 0;
}

function getLoaderObject(loader) {
  if (isString(loader)) {
    return { loader };
  }
  return loader;
}

function mergeOptions(a, b) {
  if (!b) return a;
  Object.keys(b).forEach(key => {
    a[key] = b[key];
  });
  return a;
}

function isString(a) {
  return typeof a === 'string';
}

function isFunction(a) {
  return typeof a === 'function';
}

function isType(type, obj) {
  return Object.prototype.toString.call(obj) === `[object ${type}]`;
}