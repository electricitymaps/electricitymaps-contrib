import { atom } from 'jotai';

type ModalType = 'settings' | 'layers' | null;

const activeModalAtom = atom<ModalType>(null);

export const isSettingsModalOpenAtom = atom(
  (get) => get(activeModalAtom) === 'settings',
  (_, set) => set(activeModalAtom, 'settings')
);

export const isLayersModalOpenAtom = atom(
  (get) => get(activeModalAtom) === 'layers',
  (_, set) => set(activeModalAtom, 'layers')
);
