import { useState } from "react";
import { useNotesStore } from "../../../lib/notesStore";

export default function NotesWidget() {
  const notes = useNotesStore((s) => s.notes);
  const addNote = useNotesStore((s) => s.addNote);
  const updateNote = useNotesStore((s) => s.updateNote);
  const removeNote = useNotesStore((s) => s.removeNote);
  const [draft, setDraft] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (!draft.trim()) return;
    addNote(draft.trim());
    setDraft("");
  };

  return (
    <div className="blurBg w-80 p-3.5 flex flex-col gap-3 text-zinc-100">
      <div className="flex items-center gap-2.5">
        <div className="h-9 w-9 rounded-lg bg-amber-400/20 border border-amber-400/30 flex items-center justify-center">
          <i className="bx bx-note text-lg text-amber-300" />
        </div>
        <div className="flex-1">
          <p className="font-semibold leading-tight">Quick Notes</p>
          <p className="text-[11px] text-zinc-400">{notes.length} saved</p>
        </div>
      </div>

      <form onSubmit={submit} className="flex items-center gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Write a note..."
          className="flex-1 h-9 rounded-lg bg-black/30 border border-white/10 px-2.5 text-sm outline-none focus:border-amber-400/60 placeholder:text-zinc-600"
        />
        <button
          type="submit"
          className="h-9 w-9 rounded-lg bg-amber-500/80 hover:bg-amber-500 flex items-center justify-center text-zinc-900"
          title="Add note"
        >
          <i className="bx bx-plus text-lg" />
        </button>
      </form>

      <div className="flex flex-col gap-2 max-h-56 overflow-y-auto my-scroll">
        {notes.map((note) => (
          <div
            key={note.id}
            className="group rounded-lg border border-white/10 bg-white/5 p-2.5 text-sm"
          >
            {editingId === note.id ? (
              <div className="flex flex-col gap-2">
                <textarea
                  autoFocus
                  rows={2}
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full resize-none rounded-lg bg-black/30 border border-white/10 px-2 py-1.5 text-sm outline-none focus:border-amber-400/60"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setEditingId(null)}
                    className="px-2 py-1 rounded-md text-xs text-zinc-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      updateNote(note.id, editText.trim() || note.text);
                      setEditingId(null);
                    }}
                    className="px-2 py-1 rounded-md text-xs bg-amber-500/80 text-zinc-900 font-semibold"
                  >
                    Save
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-2">
                <p className="flex-1 break-words whitespace-pre-wrap text-zinc-200">
                  {note.text}
                </p>
                <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition">
                  <button
                    onClick={() => {
                      setEditingId(note.id);
                      setEditText(note.text);
                    }}
                    className="h-6 w-6 rounded-md text-zinc-400 hover:bg-white/10 hover:text-white"
                  >
                    <i className="bx bx-pencil" />
                  </button>
                  <button
                    onClick={() => removeNote(note.id)}
                    className="h-6 w-6 rounded-md text-zinc-400 hover:bg-rose-500/70 hover:text-white"
                  >
                    <i className="bx bx-trash" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {notes.length === 0 && (
          <p className="text-xs text-zinc-500 text-center py-3">
            No notes yet — jot something down.
          </p>
        )}
      </div>
    </div>
  );
}
