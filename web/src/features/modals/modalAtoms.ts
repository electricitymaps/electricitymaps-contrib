import { atom } from 'jotai';

type ModalType = 'settings' | 'layers' | null;
enum MODAL_TYPES {
  SETTINGS = 'settings',
  LAYERS = 'layers',
}

const activeModalAtom = atom<ModalType>(null);

export const isSettingsModalOpenAtom = atom(
  (get) => get(activeModalAtom) === MODAL_TYPES.SETTINGS,
  (get, set, value?: boolean) => {
    if (value === false) {
      set(activeModalAtom, null);
    } else {
      set(
        activeModalAtom,
        get(activeModalAtom) === MODAL_TYPES.SETTINGS ? null : MODAL_TYPES.SETTINGS
      );
    }
  }
);

export const isLayersModalOpenAtom = atom(
  (get) => get(activeModalAtom) === MODAL_TYPES.LAYERS,
  (get, set, value?: boolean) => {
    if (value === false) {
      set(activeModalAtom, null);
    } else {
      set(
        activeModalAtom,
        get(activeModalAtom) === MODAL_TYPES.LAYERS ? null : MODAL_TYPES.LAYERS
      );
    }
  }
);
