const saveKey = (key: any, val: any) => {
  window.localStorage.setItem(key, val);
};

const getKey = (key: any) => {
  return window.localStorage.getItem(key);
};

export { saveKey, getKey };
