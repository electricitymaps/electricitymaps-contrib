import { getKey } from '../helpers/storage';
import { LANGUAGE_NAMES } from '../helpers/constants';

export const getPreferredLanguage = () => {
  const preferredLanguage = getKey('i18nextLng');
  return LANGUAGE_NAMES[preferredLanguage];
};
