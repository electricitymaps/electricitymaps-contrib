export const truncateWithEllipsesIfLengthExceeds = (text, maxLength) => {
  return text.length > maxLength ? `${text.substr(0, maxLength - 1)}...` : text;
};
