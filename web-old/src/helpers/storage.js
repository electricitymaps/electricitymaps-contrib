const saveKey = (key, val) => {
  window.localStorage.setItem(key, val);
};

const getKey = (key) => {
  return window.localStorage.getItem(key);
};

export { saveKey, getKey };
