import { atom } from 'jotai';

type ModalType = 'settings' | 'layers' | null;

const activeModalAtom = atom<ModalType>(null);

export const isSettingsModalOpenAtom = atom(
  (get) => get(activeModalAtom) === 'settings',
  (get, set, value?: boolean) => {
    if (value === false) {
      set(activeModalAtom, null);
    } else {
      set(activeModalAtom, get(activeModalAtom) === 'settings' ? null : 'settings');
    }
  }
);

export const isLayersModalOpenAtom = atom(
  (get) => get(activeModalAtom) === 'layers',
  (get, set, value?: boolean) => {
    if (value === false) {
      set(activeModalAtom, null);
    } else {
      set(activeModalAtom, get(activeModalAtom) === 'layers' ? null : 'layers');
    }
  }
);
