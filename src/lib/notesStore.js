import { create } from "zustand";
import { loadValue, saveValue } from "./persistence";

export const NOTES_KEY = "stickyNotes";

const uid = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

const normalize = (raw) => {
  if (!raw || typeof raw !== "object") return null;
  const text = String(raw.text ?? "").trim();
  if (!text) return null;
  return {
    id: raw.id || uid(),
    text,
    createdAt: raw.createdAt || new Date().toISOString(),
  };
};

export const useNotesStore = create((set, get) => ({
  notes: [],
  hydrated: false,

  hydrate: async () => {
    if (get().hydrated) return;
    const stored = await loadValue(NOTES_KEY);
    set({
      notes: Array.isArray(stored) ? stored.map(normalize).filter(Boolean) : [],
      hydrated: true,
    });
  },

  addNote: (text) => {
    const note = normalize({ text });
    if (!note) return;
    set((state) => ({ notes: [note, ...state.notes] }));
  },

  updateNote: (id, text) =>
    set((state) => ({
      notes: state.notes.map((n) => (n.id === id ? { ...n, text } : n)),
    })),

  removeNote: (id) =>
    set((state) => ({ notes: state.notes.filter((n) => n.id !== id) })),
}));

let persistTimer;
useNotesStore.subscribe((state, prev) => {
  if (!state.hydrated || state.notes === prev.notes) return;
  clearTimeout(persistTimer);
  persistTimer = setTimeout(() => saveValue(NOTES_KEY, state.notes), 250);
});
